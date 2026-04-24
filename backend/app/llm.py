from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from collections import OrderedDict

import httpx
from pydantic import BaseModel, ValidationError

from app.config import Settings
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
from app.models import ExtractionResult, IngestedSource, ProviderUsage


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


class ProviderError(RuntimeError):
    pass


class LlmExtractionPayload(BaseModel):
    demand: Demand
    quality: Quality


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
    if value.upper() in {"ASAP", "TBD"}:
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


def _extract_json_string(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ProviderError("Model response did not contain a JSON object.")
    return stripped[start : end + 1]


def _extract_message_text(payload: dict) -> str:
    choices = payload.get("choices") or []
    if not choices:
        raise ProviderError("Provider response did not contain any choices.")
    message = choices[0].get("message") or {}
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_parts = []
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                text_parts.append(part.get("text", ""))
        if text_parts:
            return "\n".join(text_parts)
    raise ProviderError("Provider response did not contain text content.")


def _build_provider_result(
    source: IngestedSource,
    payload: LlmExtractionPayload,
    model_name: str,
    prompt_version: str,
) -> ExtractionResult:
    return ExtractionResult(
        record=ConsultingRequestV1(
            request_id=source.request_id,
            source=source.source,
            content=source.content,
            demand=payload.demand,
            quality=payload.quality,
            processing=Processing(
                processed_at="1970-01-01T00:00:00Z",
                extractor_model=model_name,
                prompt_version=prompt_version,
            ),
        )
    )


class ExtractorProvider(ABC):
    @abstractmethod
    def extract_structured_request(self, source: IngestedSource) -> ExtractionResult:
        raise NotImplementedError


class MockExtractorProvider(ExtractorProvider):
    def __init__(
        self,
        model_name: str = "mock-extractor-v1",
        prompt_version: str = "consulting_request_v1_mock",
    ) -> None:
        self.model_name = model_name
        self.prompt_version = prompt_version

    def extract_structured_request(self, source: IngestedSource) -> ExtractionResult:
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

        payload = LlmExtractionPayload(
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
        )
        return _build_provider_result(
            source, payload, self.model_name, self.prompt_version
        )


class OpenAICompatibleExtractorProvider(ExtractorProvider):
    def __init__(
        self,
        base_url: str,
        api_key: str,
        model_name: str,
        prompt_version: str,
        timeout_seconds: float = 30.0,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model_name = model_name
        self.prompt_version = prompt_version
        self.http_client = http_client or httpx.Client(timeout=timeout_seconds)

    def _build_messages(self, source: IngestedSource) -> list[dict[str, str]]:
        schema = json.dumps(
            LlmExtractionPayload.model_json_schema(), ensure_ascii=False
        )
        source_payload = json.dumps(
            {
                "request_id": source.request_id,
                "source": source.source.model_dump(mode="json"),
                "content": source.content.model_dump(mode="json"),
                "extracted_text": source.extracted_text,
            },
            ensure_ascii=False,
        )
        system_prompt = (
            "You analyze consulting demand from arbitrary input formats. "
            "The backend may provide raw text, HTML, Markdown, PDFs, CSV/TSV, or unknown JSON exports. "
            "Infer whether the source appears to be an email, web page, document, portal posting, "
            "chat message, manual note, or other source. "
            "When a JSON or export-like input contains fields such as subject, date, from, sender, body, "
            "html, text, attachments, or url, use those fields as evidence for source and content metadata. "
            "Use export date fields for source.received_at when clearly present. "
            "Use subject/title/name fields for content.title when clearly present. "
            "Return JSON only. Use the provided schema strictly. "
            "Do not invent facts. Prefer nulls or warnings when data is unclear."
        )
        user_prompt = (
            f"Prompt version: {self.prompt_version}\n"
            "Return a JSON object matching this schema:\n"
            f"{schema}\n\n"
            "Source payload:\n"
            f"{source_payload}"
        )
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    def extract_structured_request(self, source: IngestedSource) -> ExtractionResult:
        response = self.http_client.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model_name,
                "temperature": 0,
                "response_format": {"type": "json_object"},
                "messages": self._build_messages(source),
            },
        )
        response.raise_for_status()
        payload = response.json()
        usage_payload = payload.get("usage") or {}
        content = _extract_message_text(payload)
        try:
            parsed = json.loads(_extract_json_string(content))
        except json.JSONDecodeError as exc:
            raise ProviderError("Model returned invalid JSON.") from exc
        try:
            extraction = LlmExtractionPayload.model_validate(parsed)
        except ValidationError as exc:
            raise ProviderError(
                "Model response did not match extraction schema."
            ) from exc
        result = _build_provider_result(
            source, extraction, self.model_name, self.prompt_version
        )
        if any(
            usage_payload.get(key) is not None
            for key in ["prompt_tokens", "completion_tokens", "total_tokens"]
        ):
            result.usage = ProviderUsage(
                input_tokens=usage_payload.get("prompt_tokens"),
                output_tokens=usage_payload.get("completion_tokens"),
                total_tokens=usage_payload.get("total_tokens"),
            )
        return result


def build_extractor_provider(settings: Settings) -> ExtractorProvider:
    if settings.llm_provider == "mock":
        return MockExtractorProvider(
            model_name=settings.llm_model,
            prompt_version=settings.prompt_version,
        )
    if settings.llm_provider == "openai_compatible":
        if not settings.llm_base_url:
            raise ProviderError(
                "MARKET_PULSE_LLM_BASE_URL is required for openai_compatible provider."
            )
        if not settings.llm_api_key:
            raise ProviderError(
                "MARKET_PULSE_LLM_API_KEY is required for openai_compatible provider."
            )
        return OpenAICompatibleExtractorProvider(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
            model_name=settings.llm_model,
            prompt_version=settings.prompt_version,
            timeout_seconds=settings.llm_timeout_seconds,
        )
    raise ProviderError(f"Unsupported LLM provider: {settings.llm_provider}")
