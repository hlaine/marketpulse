from __future__ import annotations

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile

from app.config import Settings, get_settings
from app.models import ExtractionRequest
from app.pipeline import ExtractionPipeline


def create_app(settings: Settings | None = None) -> FastAPI:
    active_settings = settings or get_settings()
    pipeline = ExtractionPipeline(active_settings)

    app = FastAPI(title=active_settings.app_name)

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
            temp_path = active_settings.storage_root / "raw" / f"upload-{file.filename}"
            temp_path.parent.mkdir(parents=True, exist_ok=True)
            temp_path.write_bytes(await file.read())
            return pipeline.process_file(temp_path)
        if text:
            return pipeline.process_text_request(
                ExtractionRequest(title=title, text=text)
            )
        raise HTTPException(
            status_code=400, detail="Provide either a file upload or text payload."
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

    return app


app = create_app()
