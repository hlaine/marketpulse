from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from app.config import Settings
from app.contracts import ConsultingRequestV1, Processing
from app.ingest import ingest_file, ingest_text_payload
from app.llm import ExtractorProvider, build_extractor_provider
from app.models import ExtractionRequest, ExtractionResult, IngestedSource
from app.storage import SQLiteStorage


class ExtractionPipeline:
    def __init__(
        self,
        settings: Settings,
        provider: ExtractorProvider | None = None,
        storage: SQLiteStorage | None = None,
    ) -> None:
        self.settings = settings
        self.provider = provider or build_extractor_provider(settings)
        self.storage = storage or SQLiteStorage(settings.database_path)

    def process_ingested(self, source: IngestedSource) -> ExtractionResult:
        result = self.provider.extract_structured_request(source)
        result.record.processing = Processing(
            processed_at=datetime.now(timezone.utc)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z"),
            extractor_model=self.settings.llm_model,
            prompt_version=self.settings.prompt_version,
        )
        self.storage.save(result.record)
        return result

    def process_file(
        self,
        path: str | Path,
        title: str | None = None,
        received_at: str | None = None,
        source_ref: str | None = None,
    ) -> ConsultingRequestV1:
        return self.process_ingested(
            ingest_file(
                path,
                title=title,
                received_at=received_at,
                source_ref=source_ref,
            )
        ).record

    def process_file_with_metadata(
        self,
        path: str | Path,
        title: str | None = None,
        received_at: str | None = None,
        source_ref: str | None = None,
    ) -> ExtractionResult:
        return self.process_ingested(
            ingest_file(
                path,
                title=title,
                received_at=received_at,
                source_ref=source_ref,
            )
        )

    def process_text_request(self, payload: ExtractionRequest) -> ConsultingRequestV1:
        return self.process_ingested(ingest_text_payload(payload)).record
