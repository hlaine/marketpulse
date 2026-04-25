from __future__ import annotations

import hashlib
import json
import random
import re
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import httpx
from pydantic import ValidationError

from app.config import REPO_ROOT, Settings
from app.models import DemoEmailResponse, EmailEnvelope


ROLE_TECHNOLOGIES: dict[str, list[str]] = {
    "Backend Engineer": ["Java", "AWS", "Docker", "Kafka", "PostgreSQL"],
    "Data Engineer": ["Python", "BigQuery", "Kafka", "PostgreSQL", "Docker"],
    "Frontend Engineer": ["TypeScript", "Azure", "Docker", "AWS", "PostgreSQL"],
    "Fullstack Engineer": ["TypeScript", "Java", "AWS", "PostgreSQL", "Docker"],
    "Platform Engineer": ["Kubernetes", "AWS", "Docker", "Go", "PostgreSQL"],
    "Machine Learning Engineer": ["Python", "PyTorch", "TensorFlow", "Hugging Face", "OpenAI API"],
    "AI Engineer": ["Python", "OpenAI API", "LangChain", "RAG", "Pinecone"],
    ".NET Developer": [".NET", "Azure", "Docker", "TypeScript", "PostgreSQL"],
    "Go Developer": ["Go", "Kubernetes", "AWS", "PostgreSQL", "Docker"],
    "Java Developer": ["Java", "AWS", "Kafka", "PostgreSQL", "Docker"],
}

CLIENTS = [
    ("NordKart", "e-handel"),
    ("SveaPay", "fintech"),
    ("MedCore", "healthcare"),
    ("GameForge Nordic", "gaming"),
    ("Stadspartner", "offentlig sektor"),
    ("TeleMera", "telekom och media"),
]

CITIES = ["Stockholm", "Göteborg", "Malmö"]
REMOTE_MODES = [
    ("hybrid", "hybrid"),
    ("remote", "distans"),
    ("onsite", "på plats"),
]
SENIORITIES = [
    ("Senior", "senior"),
    ("Erfaren", "mid"),
    ("Lead", "lead"),
]
SENDERS = [
    ("Viktor Olsson", "ByteForce", "byteforce.se", "Tech Recruitment Lead"),
    ("Emma Lind", "Konsult Partners", "konsultpartners.se", "Partner Manager"),
    ("Noah Berg", "NordStaff AB", "nordstaff.se", "Assignment Coordinator"),
    ("Maja Dahl", "TechLink Sweden", "techlink.se", "Senior Consultant Broker"),
]


class DemoEmailGenerator:
    def __init__(
        self,
        settings: Settings,
        data_dir: Path | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.settings = settings
        self.data_dir = data_dir or REPO_ROOT / "data" / "emails"
        self.http_client = http_client

    def generate(self, seed: str | None = None) -> DemoEmailResponse:
        run_seed = seed or _new_run_seed()
        warnings: list[str] = []
        if self._can_use_ai():
            try:
                return DemoEmailResponse(
                    email=self._generate_with_ai(run_seed),
                    generated_by="ai",
                    warnings=[],
                )
            except (httpx.HTTPError, ValidationError, ValueError, KeyError) as exc:
                warnings.append(
                    f"AI generation failed; used fallback generator ({exc.__class__.__name__})."
                )

        return DemoEmailResponse(
            email=self._generate_fallback(run_seed),
            generated_by="fallback",
            warnings=warnings,
        )

    def _can_use_ai(self) -> bool:
        return bool(
            self.settings.llm_provider == "openai_compatible"
            and self.settings.llm_base_url
            and self.settings.llm_api_key
        )

    def _generate_with_ai(self, seed: str | None) -> EmailEnvelope:
        client = self.http_client or httpx.Client(timeout=self.settings.llm_timeout_seconds)
        response = client.post(
            f"{self.settings.llm_base_url.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {self.settings.llm_api_key}"},
            json={
                "model": self.settings.llm_model,
                "temperature": 0.8,
                "response_format": {"type": "json_object"},
                "messages": self._build_ai_messages(seed),
            },
        )
        response.raise_for_status()
        content = _extract_message_text(response.json())
        payload = json.loads(_extract_json_string(content))
        return self._validate_ai_email(payload, seed)

    def _build_ai_messages(self, seed: str | None) -> list[dict[str, str]]:
        examples = self._load_style_examples(limit=4)
        variation = _build_variation(seed or _new_run_seed())
        system_prompt = (
            "You generate realistic demo emails for a Swedish consulting demand product. "
            "Return JSON only with keys id, date, subject, from, to, cc, body. "
            "The body must be HTML similar to the examples and describe one consulting request. "
            "Include role, seniority, client sector, start, duration, location/remote mode, rate, "
            "and exactly three requested technologies. "
            "Use the variation anchors exactly so every refresh creates a noticeably different email. "
            "Do not include markdown."
        )
        user_prompt = (
            f"Generation seed: {seed or 'none'}\n"
            "Variation anchors to use exactly:\n"
            f"{json.dumps(variation, ensure_ascii=False)}\n"
            "Use this style from existing demo data:\n"
            f"{json.dumps(examples, ensure_ascii=False)}"
        )
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    def _load_style_examples(self, limit: int) -> list[dict[str, str | None]]:
        examples: list[dict[str, str | None]] = []
        for path in sorted(self.data_dir.glob("*.json"))[:limit]:
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                envelope = EmailEnvelope.model_validate(payload)
            except (OSError, json.JSONDecodeError, ValidationError):
                continue
            examples.append(
                {
                    "subject": envelope.subject,
                    "from": envelope.from_,
                    "body": _compact_html(envelope.body or "")[:900],
                }
            )
        return examples

    def _validate_ai_email(self, payload: dict[str, Any], seed: str | None) -> EmailEnvelope:
        envelope = EmailEnvelope.model_validate(payload)
        if not envelope.subject or not envelope.from_ or not envelope.body:
            raise ValueError("AI email is missing subject, sender, or body.")
        payload["id"] = _demo_id(seed)
        payload["date"] = _normalize_demo_date(envelope.date, seed)
        payload["to"] = "inbox@dummy.se"
        payload["cc"] = ""
        return EmailEnvelope.model_validate(payload)

    def _generate_fallback(self, seed: str | None) -> EmailEnvelope:
        variation = _build_variation(seed or _new_run_seed())
        role = variation["role"]
        technologies = variation["technologies"]
        client_name = variation["client_name"]
        sector = variation["sector"]
        city = variation["city"]
        remote_normalized = variation["remote_mode"]
        remote_label = variation["remote_label"]
        seniority_label = variation["seniority_label"]
        seniority_normalized = variation["seniority"]
        duration_months = variation["duration_months"]
        rate = variation["rate"]
        sender_name = variation["sender_name"]
        sender_org = variation["sender_organization"]
        sender_domain = variation["sender_domain"]
        sender_title = variation["sender_title"]
        urgent = variation["subject_prefix"]
        subject = f"{urgent}: {role}"
        body = _fallback_body(
            client_name=client_name,
            sector=sector,
            role=role,
            seniority_label=seniority_label,
            seniority_normalized=seniority_normalized,
            city=city,
            remote_label=remote_label,
            remote_normalized=remote_normalized,
            duration_months=duration_months,
            rate=rate,
            technologies=technologies,
            sender_name=sender_name,
            sender_org=sender_org,
            sender_title=sender_title,
        )
        return EmailEnvelope.model_validate(
            {
                "id": _demo_id(seed),
                "date": _demo_date(seed),
                "subject": subject,
                "from": f"{sender_name} <{_email_local_part(sender_name)}@{sender_domain}>",
                "to": "inbox@dummy.se",
                "cc": "",
                "body": body,
            }
        )


def _new_run_seed() -> str:
    return f"demo-refresh-{datetime.now(timezone.utc).isoformat()}-{uuid.uuid4().hex}"


def _build_variation(seed: str) -> dict[str, Any]:
    rng = random.Random(seed)
    role = rng.choice(list(ROLE_TECHNOLOGIES))
    technologies = rng.sample(ROLE_TECHNOLOGIES[role], 3)
    client_name, sector = rng.choice(CLIENTS)
    remote_normalized, remote_label = rng.choice(REMOTE_MODES)
    seniority_label, seniority_normalized = rng.choice(SENIORITIES)
    sender_name, sender_org, sender_domain, sender_title = rng.choice(SENDERS)
    return {
        "role": role,
        "technologies": technologies,
        "client_name": client_name,
        "sector": sector,
        "city": rng.choice(CITIES),
        "remote_mode": remote_normalized,
        "remote_label": remote_label,
        "seniority_label": seniority_label,
        "seniority": seniority_normalized,
        "duration_months": rng.choice([3, 6, 9, 12]),
        "rate": rng.choice([750, 800, 850, 900, 950, 1050]),
        "sender_name": sender_name,
        "sender_organization": sender_org,
        "sender_domain": sender_domain,
        "sender_title": sender_title,
        "subject_prefix": rng.choice(["Ny förfrågan", "Nytt uppdrag", "ASAP", "New Request"]),
    }


def _fallback_body(
    *,
    client_name: str,
    sector: str,
    role: str,
    seniority_label: str,
    seniority_normalized: str,
    city: str,
    remote_label: str,
    remote_normalized: str,
    duration_months: int,
    rate: int,
    technologies: list[str],
    sender_name: str,
    sender_org: str,
    sender_title: str,
) -> str:
    technology_items = "".join(f"<li>{technology}</li>" for technology in technologies)
    return (
        "<html><body>\n"
        "<p>Hej,</p>\n"
        f"<p>Vi har precis fått in ett uppdrag från {client_name}, ett bolag verksamt inom {sector}.</p>\n"
        f"<p>De söker en {seniority_label.lower()} {role} för att förstärka sitt teknikteam.</p>\n"
        "<p>Uppdragsdetaljer:</p>\n"
        "<ul>"
        f"<li>ROLE: {seniority_normalized} {role}</li>"
        "<li>Start: ASAP</li>"
        f"<li>Längd: {duration_months} månader</li>"
        f"<li>Plats: {city} ({remote_label})</li>"
        f"<li>Remote mode: {remote_normalized}</li>"
        f"<li>Ersättning: {rate} kr/h</li>"
        "</ul>\n"
        "<p>Kompetens som efterfrågas:</p>\n"
        f"<ul>{technology_items}</ul>\n"
        "<p>Tveka inte att höra av dig om du vill veta mer!</p>\n"
        f"<p>Med vänlig hälsning,<br>\n{sender_name}<br>\n{sender_title}<br>\n{sender_org}</p>\n"
        "</body></html>"
    )


def _demo_id(seed: str | None) -> str:
    if seed:
        digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:12]
        return f"demo-{digest}"
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    suffix = random.SystemRandom().randrange(1000, 9999)
    return f"demo-{timestamp}-{suffix}"


def _demo_date(seed: str | None) -> str:
    if seed:
        rng = random.Random(seed)
        base = datetime(2026, 4, 25, 8, 0, tzinfo=timezone.utc)
        value = base + timedelta(minutes=rng.randrange(0, 720))
    else:
        value = datetime.now(timezone.utc)
    return value.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _normalize_demo_date(value: str | None, seed: str | None) -> str:
    if not value:
        return _demo_date(seed)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return _demo_date(seed)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return (
        parsed.astimezone(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _email_local_part(name: str) -> str:
    return ".".join(part.lower() for part in name.split())


def _compact_html(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _extract_json_string(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("Model response did not contain a JSON object.")
    return stripped[start : end + 1]


def _extract_message_text(payload: dict[str, Any]) -> str:
    choices = payload.get("choices") or []
    if not choices:
        raise ValueError("Provider response did not contain choices.")
    message = choices[0].get("message") or {}
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_parts = [
            part.get("text", "")
            for part in content
            if isinstance(part, dict) and part.get("type") == "text"
        ]
        if text_parts:
            return "\n".join(text_parts)
    raise ValueError("Provider response did not contain text content.")
