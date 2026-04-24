from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


SourceKind = Literal[
    "email",
    "web_page",
    "document",
    "portal_posting",
    "chat_message",
    "manual_note",
    "other",
]
ContentPartKind = Literal[
    "title", "message", "document", "attachment", "web_page", "metadata", "other"
]
TechnologyCategory = Literal[
    "language", "framework", "cloud", "database", "tool", "platform", "other"
]
Importance = Literal["required", "preferred", "mentioned"]
ReviewStatus = Literal["ok", "partial", "needs_review", "failed"]


class Evidence(BaseModel):
    snippet: str
    source_part: ContentPartKind


class TaggedValue(BaseModel):
    raw: str | None
    normalized: str | None
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[Evidence] = Field(default_factory=list)


class TechnologyValue(BaseModel):
    raw: str
    normalized: str | None
    category: TechnologyCategory
    importance: Importance | None
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[Evidence] = Field(default_factory=list)


class CertificationValue(BaseModel):
    raw: str | None
    normalized: str | None
    importance: Importance | None
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[Evidence] = Field(default_factory=list)


class LanguageRequirement(BaseModel):
    raw: str
    normalized: str | None
    proficiency: Literal["basic", "professional", "fluent", "native"] | None = None
    importance: Importance | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[Evidence] = Field(default_factory=list)


class Source(BaseModel):
    kind: SourceKind
    source_ref: str
    received_at: str | None
    sender_name: str | None
    sender_organization: str | None
    sender_domain: str | None
    origin_url: str | None
    content_types: list[str] = Field(default_factory=list)


class ContentPart(BaseModel):
    part_id: str
    kind: ContentPartKind
    mime_type: str | None
    text_excerpt: str | None


class Content(BaseModel):
    title: str | None
    language: str | None
    parts: list[ContentPart] = Field(default_factory=list)


class LocationValue(BaseModel):
    raw: str | None
    city: str | None
    country: str | None
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[Evidence] = Field(default_factory=list)


class Commercial(BaseModel):
    start_date: str | None
    start_date_raw: str | None
    duration_raw: str | None
    duration_months: int | None
    allocation_percent: int | None
    positions_count: int | None
    rate_amount: int | None
    rate_currency: str | None
    rate_unit: Literal["hour", "day", "month"] | None
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[Evidence] = Field(default_factory=list)


class Summary(BaseModel):
    text: str
    confidence: float = Field(ge=0.0, le=1.0)


class Demand(BaseModel):
    primary_role: TaggedValue
    secondary_roles: list[TaggedValue] = Field(default_factory=list)
    seniority: TaggedValue
    technologies: list[TechnologyValue] = Field(default_factory=list)
    certifications: list[CertificationValue] = Field(default_factory=list)
    languages: list[LanguageRequirement] = Field(default_factory=list)
    sector: TaggedValue
    location: LocationValue
    remote_mode: TaggedValue
    commercial: Commercial
    summary: Summary


class Quality(BaseModel):
    overall_confidence: float = Field(ge=0.0, le=1.0)
    review_status: ReviewStatus
    warnings: list[str] = Field(default_factory=list)


class Processing(BaseModel):
    processed_at: str
    extractor_model: str
    prompt_version: str


class ConsultingRequestV1(BaseModel):
    schema_version: str = "1.0"
    request_id: str
    source: Source
    content: Content
    demand: Demand
    quality: Quality
    processing: Processing


def export_contract_schema(output_path: Path) -> None:
    output_path.write_text(
        ConsultingRequestV1.model_json_schema_json(indent=2), encoding="utf-8"
    )
