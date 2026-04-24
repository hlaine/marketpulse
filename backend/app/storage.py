from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from app.contracts import ConsultingRequestV1
from app.models import IndexEntry, IngestedSource, StoredRecord


class FileStorage:
    def __init__(self, storage_root: Path) -> None:
        self.storage_root = storage_root
        self.requests_dir = storage_root / "requests"
        self.raw_dir = storage_root / "raw"
        self.index_dir = storage_root / "index"
        self.index_path = self.index_dir / "requests.json"
        self.requests_dir.mkdir(parents=True, exist_ok=True)
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        if not self.index_path.exists():
            self.index_path.write_text("[]\n", encoding="utf-8")

    def save(self, record: ConsultingRequestV1, source: IngestedSource) -> StoredRecord:
        record_path = self.requests_dir / f"{record.request_id}.json"
        record_path.write_text(record.model_dump_json(indent=2), encoding="utf-8")

        raw_payload_path = None
        raw_record_dir = self.raw_dir / record.request_id
        raw_record_dir.mkdir(parents=True, exist_ok=True)
        raw_payload_path = raw_record_dir / "source.json"
        raw_payload_path.write_text(
            json.dumps(source.raw_payload or {}, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        (raw_record_dir / "extracted_text.txt").write_text(
            source.extracted_text, encoding="utf-8"
        )

        self._upsert_index(record)
        return StoredRecord(
            record=record, raw_payload_path=raw_payload_path, record_path=record_path
        )

    def _upsert_index(self, record: ConsultingRequestV1) -> None:
        stored_at = (
            datetime.now(timezone.utc)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z")
        )
        entry = IndexEntry(
            request_id=record.request_id,
            received_at=record.source.received_at,
            source_kind=record.source.kind,
            primary_role=record.demand.primary_role.normalized,
            sector=record.demand.sector.normalized,
            location_city=record.demand.location.city,
            review_status=record.quality.review_status,
            overall_confidence=record.quality.overall_confidence,
            stored_at=stored_at,
        )
        entries = self.list_requests()
        updated = [
            existing for existing in entries if existing.request_id != record.request_id
        ]
        updated.append(entry)
        updated.sort(key=lambda item: item.received_at or "", reverse=True)
        self.index_path.write_text(
            json.dumps([item.model_dump() for item in updated], indent=2),
            encoding="utf-8",
        )

    def list_requests(self) -> list[IndexEntry]:
        payload = json.loads(self.index_path.read_text(encoding="utf-8"))
        return [IndexEntry.model_validate(item) for item in payload]

    def get_request(self, request_id: str) -> ConsultingRequestV1:
        record_path = self.requests_dir / f"{request_id}.json"
        payload = json.loads(record_path.read_text(encoding="utf-8"))
        return ConsultingRequestV1.model_validate(payload)
