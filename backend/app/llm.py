from __future__ import annotations

import re
from abc import ABC, abstractmethod
from collections import OrderedDict

from app.contracts import (
    Commercial,
    ConsultingRequestV1,
    Demand,
    Evidence,
    LocationValue,
    Processing,
    Quality,
    Summary,
    TaggedValue,
    TechnologyValue,
)
from app.models import IngestedSource


ROLE_PATTERNS = [
    ".NET Developer",
    "Machine Learning Engineer",
    "Microservices Engineer",
    "Infrastructure Engineer",
    "Frontend Engineer",
    "Fullstack Engineer",
    "Platform Engineer",
    "Backend Engineer",
    "Backend Developer",
    "Software Engineer",
    "Systems Engineer",
    "Data Engineer",
    "Web Developer",
    "Java Developer",
    "Go Developer",
    "Python Developer",
    "Scala Developer",
    "Kotlin Developer",
    "PHP Developer",
    "AI Engineer",
]

TECH_CATALOG: OrderedDict[str, tuple[str, str]] = OrderedDict(
    [
        ("OpenAI API", ("OpenAI API", "tool")),
        ("Hugging Face", ("Hugging Face", "tool")),
        ("LangChain", ("LangChain", "framework")),
        ("LlamaIndex", ("LlamaIndex", "framework")),
        ("TensorFlow", ("TensorFlow", "framework")),
        ("PyTorch", ("PyTorch", "framework")),
        ("Pinecone", ("Pinecone", "database")),
        ("BigQuery", ("BigQuery", "database")),
        ("PostgreSQL", ("PostgreSQL", "database")),
        ("MongoDB", ("MongoDB", "database")),
        ("MySQL", ("MySQL", "database")),
        ("Oracle", ("Oracle", "database")),
        ("DynamoDB", ("DynamoDB", "database")),
        ("Cassandra", ("Cassandra", "database")),
        ("Kafka", ("Kafka", "tool")),
        ("RabbitMQ", ("RabbitMQ", "tool")),
        ("Redis", ("Redis", "database")),
        ("SQS", ("SQS", "tool")),
        ("Docker Compose", ("Docker Compose", "tool")),
        ("Docker", ("Docker", "tool")),
        ("Kubernetes", ("Kubernetes", "platform")),
        ("AWS", ("AWS", "cloud")),
        ("Azure", ("Azure", "cloud")),
        ("GCP", ("GCP", "cloud")),
        ("AI/ML", ("AI/ML", "platform")),
        ("Java", ("Java", "language")),
        ("TypeScript", ("TypeScript", "language")),
        ("Python", ("Python", "language")),
        ("Go", ("Go", "language")),
        ("Kotlin", ("Kotlin", "language")),
        ("Scala", ("Scala", "language")),
        ("Rust", ("Rust", "language")),
        ("PHP", ("PHP", "language")),
        (".NET", (".NET", "framework")),
        ("RAG", ("RAG", "other")),
    ]
)

SECTOR_HINTS = {
    "public sector": "public",
    "offentlig sektor": "public",
    "public": "public",
    "fintech": "private",
    "gaming": "private",
    "e-commerce": "private",
    "e-handel": "private",
    "ehandel": "private",
    "healthcare": "private",
    "hälso- och sjukvård": "private",
    "hälso och sjukvård": "private",
    "telecom/media": "private",
    "telekom och media": "private",
}

CITY_NAMES = ["Stockholm", "Göteborg", "Malmö"]


def _make_evidence(text: str, source_part: str = "message") -> list[Evidence]:
    snippet = text.strip()
    if not snippet:
        return []
    return [Evidence(snippet=snippet[:240], source_part=source_part)]


def _search(pattern: str, text: str) -> re.Match[str] | None:
    return re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)


def _normalize_duration(text: str | None) -> tuple[str | None, int | None]:
    if not text:
        return None, None
    value = text.strip()
    match = re.search(r"(\d+)\s*(?:months?|m|månader?)", value, flags=re.IGNORECASE)
    if match:
        return value, int(match.group(1))
    if value.upper() == "TBD":
        return value, None
    return value, None


def _normalize_start(text: str | None) -> tuple[str | None, str | None]:
    if not text:
        return None, None
    value = text.strip()
    if value.upper() == "ASAP" or value.upper() == "TBD":
        return None, value
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return f"{value}T00:00:00Z", value
    return None, value


def _extract_line_value(text: str, labels: list[str]) -> str | None:
    for label in labels:
        match = _search(rf"{label}\s*:\s*([^\n|]+)", text)
        if match:
            return match.group(1).strip()
    return None


def _extract_role(text: str) -> tuple[str | None, list[Evidence]]:
    upper_text = text.replace("–", "-")
    role_line = _extract_line_value(upper_text, ["ROLE", "Roll"])
    haystacks = [role_line, upper_text]
    for haystack in haystacks:
        if not haystack:
            continue
        for role in ROLE_PATTERNS:
            if re.search(re.escape(role), haystack, flags=re.IGNORECASE):
                match = re.search(re.escape(role), haystack, flags=re.IGNORECASE)
                raw = match.group(0) if match else role
                return role, _make_evidence(role_line or raw)
    return None, []


def _extract_seniority(text: str) -> tuple[str, str | None, list[Evidence], float]:
    mappings = [
        (r"\barchitect\b", "architect"),
        (r"\btech lead\b", "lead"),
        (r"\blead\b", "lead"),
        (r"\bsenior\b", "senior"),
        (r"\bmid\b", "mid"),
        (r"\bjunior\b", "junior"),
        (r"\berfaren\b", "mid"),
    ]
    for pattern, normalized in mappings:
        match = _search(pattern, text)
        if match:
            return normalized, match.group(0), _make_evidence(match.group(0)), 0.88
    return "unknown", None, [], 0.35


def _extract_technologies(text: str) -> list[TechnologyValue]:
    technologies: list[TechnologyValue] = []
    seen: set[str] = set()
    for token, (normalized, category) in TECH_CATALOG.items():
        match = _search(rf"(?<!\w){re.escape(token)}(?!\w)", text)
        if match and normalized not in seen:
            seen.add(normalized)
            technologies.append(
                TechnologyValue(
                    raw=match.group(0),
                    normalized=normalized,
                    category=category,
                    importance="required",
                    confidence=0.9,
                    evidence=_make_evidence(match.group(0)),
                )
            )
    return technologies


def _extract_sector(text: str) -> tuple[str, str | None, list[Evidence], float]:
    lowered = text.lower()
    for raw, normalized in SECTOR_HINTS.items():
        if raw in lowered:
            return normalized, raw, _make_evidence(raw), 0.84
    return "unknown", None, [], 0.3


def _extract_location(text: str) -> tuple[LocationValue, TaggedValue]:
    raw_location = _extract_line_value(text, ["Location", "LOCATION", "Plats"])
    if not raw_location:
        return (
            LocationValue(
                raw=None, city=None, country=None, confidence=0.2, evidence=[]
            ),
            TaggedValue(raw=None, normalized="unknown", confidence=0.2, evidence=[]),
        )
    city = next(
        (city for city in CITY_NAMES if city.lower() in raw_location.lower()), None
    )
    lowered = raw_location.lower()
    if any(token in lowered for token in ["on-site", "på plats"]):
        remote = "onsite"
    elif "hybrid" in lowered:
        remote = "hybrid"
    elif any(token in lowered for token in ["remote", "distans"]):
        remote = "remote"
    else:
        remote = "unknown"
    evidence = _make_evidence(raw_location)
    return (
        LocationValue(
            raw=raw_location,
            city=city,
            country="Sweden" if city else None,
            confidence=0.9 if city else 0.5,
            evidence=evidence,
        ),
        TaggedValue(
            raw=raw_location,
            normalized=remote,
            confidence=0.9 if remote != "unknown" else 0.4,
            evidence=evidence,
        ),
    )


def _extract_commercial(text: str) -> Commercial:
    start_raw = _extract_line_value(text, ["Start", "START"])
    duration_raw = _extract_line_value(text, ["Duration", "DURATION", "Längd"])
    rate_raw = _extract_line_value(text, ["Rate", "RATE", "Ersättning", "Arvode"])
    start_date, start_date_raw = _normalize_start(start_raw)
    duration_value, duration_months = _normalize_duration(duration_raw)
    rate_amount = None
    rate_currency = None
    rate_unit = None
    evidence_bits = [part for part in [start_raw, duration_raw, rate_raw] if part]
    if rate_raw:
        amount_match = re.search(r"(\d{3,4})", rate_raw)
        if amount_match:
            rate_amount = int(amount_match.group(1))
            rate_currency = "SEK"
            rate_unit = "hour"
    return Commercial(
        start_date=start_date,
        start_date_raw=start_date_raw,
        duration_raw=duration_value,
        duration_months=duration_months,
        allocation_percent=None,
        positions_count=1,
        rate_amount=rate_amount,
        rate_currency=rate_currency,
        rate_unit=rate_unit,
        confidence=0.85 if any([start_raw, duration_raw, rate_amount]) else 0.35,
        evidence=_make_evidence(" | ".join(evidence_bits)) if evidence_bits else [],
    )


def _build_summary(
    role: str | None, city: str | None, remote_mode: str, duration_months: int | None
) -> Summary:
    role_text = role or "consulting role"
    place = city or remote_mode
    if duration_months:
        text = f"Request for a {role_text} in {place} for a {duration_months} month assignment."
    else:
        text = f"Request for a {role_text} in {place}."
    return Summary(text=text, confidence=0.82 if role else 0.45)


class ExtractorProvider(ABC):
    @abstractmethod
    def extract_structured_request(self, source: IngestedSource) -> ConsultingRequestV1:
        raise NotImplementedError


class MockExtractorProvider(ExtractorProvider):
    def __init__(
        self,
        model_name: str = "mock-extractor-v1",
        prompt_version: str = "consulting_request_v1_mock",
    ) -> None:
        self.model_name = model_name
        self.prompt_version = prompt_version

    def extract_structured_request(self, source: IngestedSource) -> ConsultingRequestV1:
        text = source.extracted_text
        role, role_evidence = _extract_role(text)
        seniority, seniority_raw, seniority_evidence, seniority_confidence = (
            _extract_seniority(text)
        )
        technologies = _extract_technologies(text)
        sector, sector_raw, sector_evidence, sector_confidence = _extract_sector(text)
        location, remote_mode = _extract_location(text)
        commercial = _extract_commercial(text)

        warnings: list[str] = []
        if not role:
            warnings.append("Primary role could not be identified confidently.")
        if sector == "unknown":
            warnings.append("Sector could not be identified confidently.")
        if location.city is None:
            warnings.append("Location city is missing or ambiguous.")

        confidences = [
            0.9 if role else 0.35,
            seniority_confidence,
            0.88 if technologies else 0.3,
            sector_confidence,
            location.confidence,
            commercial.confidence,
        ]
        overall_confidence = round(sum(confidences) / len(confidences), 2)
        review_status = (
            "ok" if overall_confidence >= 0.8 and not warnings else "partial"
        )

        return ConsultingRequestV1(
            request_id=source.request_id,
            source=source.source,
            content=source.content,
            demand=Demand(
                primary_role=TaggedValue(
                    raw=role,
                    normalized=role,
                    confidence=0.9 if role else 0.35,
                    evidence=role_evidence,
                ),
                secondary_roles=[],
                seniority=TaggedValue(
                    raw=seniority_raw,
                    normalized=seniority,
                    confidence=seniority_confidence,
                    evidence=seniority_evidence,
                ),
                technologies=technologies,
                certifications=[],
                languages=[],
                sector=TaggedValue(
                    raw=sector_raw,
                    normalized=sector,
                    confidence=sector_confidence,
                    evidence=sector_evidence,
                ),
                location=location,
                remote_mode=remote_mode,
                commercial=commercial,
                summary=_build_summary(
                    role,
                    location.city,
                    remote_mode.normalized or "unknown",
                    commercial.duration_months,
                ),
            ),
            quality=Quality(
                overall_confidence=overall_confidence,
                review_status=review_status,
                warnings=warnings,
            ),
            processing=Processing(
                processed_at="1970-01-01T00:00:00Z",
                extractor_model=self.model_name,
                prompt_version=self.prompt_version,
            ),
        )
