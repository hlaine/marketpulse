from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from app.contracts import ConsultingRequestV1, Content, Source


class EmailEnvelope(BaseModel):
    id: int | str | None = None
    date: str | None = None
    subject: str | None = None
    from_: str | None = Field(default=None, alias="from")
    to: str | None = None
    cc: str | None = None
    body: str | None = None


class IngestedSource(BaseModel):
    request_id: str
    source: Source
    content: Content
    raw_payload: dict | None = None
    extracted_text: str
    input_path: Path | None = None

    model_config = {"arbitrary_types_allowed": True}


class ExtractionRequest(BaseModel):
    title: str | None = None
    text: str
    source_ref: str | None = None
    received_at: str | None = None


class ProviderUsage(BaseModel):
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None


class ExtractionResult(BaseModel):
    record: ConsultingRequestV1
    usage: ProviderUsage | None = None


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    conversation_id: str | None = None


class ChatQueryResult(BaseModel):
    sql: str
    rows: list[dict]
    row_count: int


class ChatResponse(BaseModel):
    answer: str
    conversation_id: str | None = None
    sql: list[str] = Field(default_factory=list)
    rows: list[dict] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    usage: ProviderUsage | None = None


class StoredRecord(BaseModel):
    record: ConsultingRequestV1
    database_path: Path

    model_config = {"arbitrary_types_allowed": True}


class IndexEntry(BaseModel):
    request_id: str
    received_at: str | None
    source_kind: str
    primary_role: str | None
    sector: str | None
    location_city: str | None
    review_status: str
    overall_confidence: float
    stored_at: str
