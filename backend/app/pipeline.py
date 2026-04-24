from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from app.config import Settings
from app.contracts import ConsultingRequestV1, Processing
from app.ingest import ingest_file, ingest_text_payload
from app.llm import ExtractorProvider, MockExtractorProvider
from app.models import ExtractionRequest, IngestedSource
from app.storage import FileStorage


class ExtractionPipeline:
    def __init__(
        self,
        settings: Settings,
        provider: ExtractorProvider | None = None,
        storage: FileStorage | None = None,
    ) -> None:
        self.settings = settings
        self.provider = provider or MockExtractorProvider(
            model_name=settings.llm_model,
            prompt_version=settings.prompt_version,
        )
        self.storage = storage or FileStorage(settings.storage_root)

    def process_ingested(self, source: IngestedSource) -> ConsultingRequestV1:
        record = self.provider.extract_structured_request(source)
        record.processing = Processing(
            processed_at=datetime.now(timezone.utc)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z"),
            extractor_model=self.settings.llm_model,
            prompt_version=self.settings.prompt_version,
        )
        self.storage.save(record, source)
        return record

    def process_file(self, path: str | Path) -> ConsultingRequestV1:
        return self.process_ingested(ingest_file(path))

    def process_text_request(self, payload: ExtractionRequest) -> ConsultingRequestV1:
        return self.process_ingested(ingest_text_payload(payload))
