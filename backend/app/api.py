from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from app.chat import AnalysisChatService, ChatError, UnsafeQueryError
from app.config import Settings, get_settings
from app.llm import ProviderError
from app.models import ChatRequest, DocumentUploadResponse, ExtractionRequest
from app.pipeline import ExtractionPipeline


SUPPORTED_UPLOAD_TYPES = {
    ".json": {"application/json", "text/json", "application/octet-stream"},
    ".txt": {"text/plain", "application/octet-stream"},
    ".md": {"text/markdown", "text/plain", "application/octet-stream"},
    ".eml": {"message/rfc822", "text/plain", "application/octet-stream"},
    ".pdf": {"application/pdf", "application/octet-stream"},
}


def create_app(settings: Settings | None = None) -> FastAPI:
    active_settings = settings or get_settings()
    pipeline = ExtractionPipeline(active_settings)
    chat_service = AnalysisChatService(active_settings)

    app = FastAPI(title=active_settings.app_name)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:4200", "http://127.0.0.1:4200"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/extract")
    async def extract(
        request: Request,
        file: UploadFile | None = File(default=None),
        title: str | None = Form(default=None),
        text: str | None = Form(default=None),
    ):
        if request.headers.get("content-type", "").startswith("application/json"):
            payload = ExtractionRequest.model_validate(await request.json())
            return pipeline.process_text_request(payload)
        if file is not None:
            return await _process_upload(
                file=file,
                pipeline=pipeline,
                max_bytes=active_settings.upload_max_bytes,
                title=title,
            )
        if text:
            return pipeline.process_text_request(
                ExtractionRequest(title=title, text=text)
            )
        raise HTTPException(
            status_code=400, detail="Provide either a file upload or text payload."
        )

    @app.post("/documents", status_code=201)
    async def upload_document(
        file: UploadFile = File(...),
        title: str | None = Form(default=None),
        received_at: str | None = Form(default=None),
        source_ref: str | None = Form(default=None),
    ) -> DocumentUploadResponse:
        record = await _process_upload(
            file=file,
            pipeline=pipeline,
            max_bytes=active_settings.upload_max_bytes,
            title=title,
            received_at=received_at,
            source_ref=source_ref,
        )
        return DocumentUploadResponse(
            request_id=record.request_id,
            stored=True,
            record=record,
            warnings=record.quality.warnings,
        )

    @app.get("/requests")
    def list_requests():
        return pipeline.storage.list_requests()

    @app.get("/requests/{request_id}")
    def get_request(request_id: str):
        try:
            return pipeline.storage.get_request(request_id)
        except FileNotFoundError as exc:
            raise HTTPException(
                status_code=404, detail=f"Unknown request_id: {request_id}"
            ) from exc

    @app.post("/chat")
    def chat(payload: ChatRequest):
        try:
            return chat_service.answer(payload)
        except UnsafeQueryError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except ChatError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    return app


def _validate_upload(file: UploadFile) -> str:
    filename = Path(file.filename or "").name
    if not filename:
        raise HTTPException(status_code=400, detail="Uploaded file must have a name.")
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_UPLOAD_TYPES:
        allowed = ", ".join(sorted(SUPPORTED_UPLOAD_TYPES))
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{suffix}'. Allowed types: {allowed}.",
        )
    content_type = (file.content_type or "application/octet-stream").split(";", 1)[0]
    if content_type not in SUPPORTED_UPLOAD_TYPES[suffix]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported content type '{content_type}' for {suffix} upload.",
        )
    return filename


async def _process_upload(
    file: UploadFile,
    pipeline: ExtractionPipeline,
    max_bytes: int,
    title: str | None = None,
    received_at: str | None = None,
    source_ref: str | None = None,
):
    filename = _validate_upload(file)
    payload = await file.read(max_bytes + 1)
    if len(payload) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"Uploaded file exceeds max size of {max_bytes} bytes.",
        )
    if not payload:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    suffix = Path(filename).suffix.lower()
    effective_source_ref = source_ref or _auto_source_ref(filename, suffix, payload)
    try:
        with tempfile.TemporaryDirectory(prefix="marketpulse-upload-") as temp_dir:
            temp_path = Path(temp_dir) / filename
            temp_path.write_bytes(payload)
            return pipeline.process_file(
                temp_path,
                title=title,
                received_at=received_at,
                source_ref=effective_source_ref,
            )
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except (UnicodeDecodeError, ValueError, OSError) as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Could not read uploaded {suffix} document: {exc}",
        ) from exc
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


def _auto_source_ref(filename: str, suffix: str, payload: bytes) -> str | None:
    if suffix == ".json":
        try:
            decoded = json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None
        if isinstance(decoded, dict) and any(
            key in decoded for key in ["body", "subject", "from", "date"]
        ):
            return None
    digest = hashlib.sha1(payload).hexdigest()[:12]
    return f"upload://{digest}/{filename}"


app = create_app()
