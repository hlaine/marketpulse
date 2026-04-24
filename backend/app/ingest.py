from __future__ import annotations

import hashlib
import html
import json
import re
from email.utils import parseaddr
from pathlib import Path

from app.contracts import Content, ContentPart, Source
from app.models import EmailEnvelope, ExtractionRequest, IngestedSource


ORG_OVERRIDES = {
    "byteforce": "ByteForce",
    "konsultpartners": "Konsult Partners",
    "nordstaff": "NordStaff AB",
    "staffbridge": "Staffbridge Nordic",
    "peakrecruit": "PeakRecruit",
    "techlink": "TechLink Sweden",
    "nexum": "Nexum Consulting",
    "agileminds": "Agile Minds",
}


def _clean_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def strip_html(value: str) -> str:
    text = value.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
    text = re.sub(r"</p>|</div>|</li>|</ul>|</ol>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<li>", "• ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = text.replace("\r", "")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return "\n".join(line.strip() for line in text.splitlines()).strip()


def infer_language(text: str) -> str | None:
    lowered = text.lower()
    if any(
        token in lowered
        for token in [
            "hej",
            "med vänlig hälsning",
            "ny förfrågan",
            "uppdragsdetaljer",
            "längd",
        ]
    ):
        return "sv"
    if any(
        token in lowered
        for token in ["hello", "best regards", "new request", "assignment details"]
    ):
        return "en"
    return None


def parse_sender(sender: str | None) -> tuple[str | None, str | None, str | None]:
    if not sender:
        return None, None, None
    name, email_address = parseaddr(sender)
    domain = email_address.split("@", 1)[1].lower() if "@" in email_address else None
    org = None
    if domain:
        root = domain.split(".", 1)[0]
        org = ORG_OVERRIDES.get(root, root.replace("-", " ").title())
    return name or None, org, domain


def build_request_id(source_ref: str, raw_identifier: str | int | None = None) -> str:
    if raw_identifier is not None:
        try:
            return f"req-{int(raw_identifier):04d}"
        except (TypeError, ValueError):
            return f"req-{raw_identifier}"
    digest = hashlib.sha1(source_ref.encode("utf-8")).hexdigest()[:12]
    return f"req-{digest}"


def ingest_email_json(path: Path) -> IngestedSource:
    payload = json.loads(path.read_text(encoding="utf-8"))
    envelope = EmailEnvelope.model_validate(payload)
    body = envelope.body or ""
    body_text = strip_html(body) if "<" in body and ">" in body else body
    sender_name, sender_organization, sender_domain = parse_sender(envelope.from_)
    source_ref = f"email-json://{path.name}"
    request_id = build_request_id(source_ref, envelope.id)
    title = envelope.subject.strip() if envelope.subject else None
    combined = "\n\n".join(part for part in [title or "", body_text] if part).strip()
    return IngestedSource(
        request_id=request_id,
        source=Source(
            kind="email",
            source_ref=source_ref,
            received_at=envelope.date,
            sender_name=sender_name,
            sender_organization=sender_organization,
            sender_domain=sender_domain,
            origin_url=None,
            content_types=[
                "application/json",
                "text/plain" if body_text == body else "text/html",
            ],
        ),
        content=Content(
            title=title,
            language=infer_language(f"{title or ''}\n{body_text}"),
            parts=[
                ContentPart(
                    part_id="title",
                    kind="title",
                    mime_type="text/plain",
                    text_excerpt=title,
                ),
                ContentPart(
                    part_id="body",
                    kind="message",
                    mime_type="text/plain",
                    text_excerpt=body_text,
                ),
            ],
        ),
        raw_payload=payload,
        extracted_text=combined,
        input_path=path,
    )


def ingest_text_payload(payload: ExtractionRequest) -> IngestedSource:
    source_ref = (
        payload.source_ref
        or f"manual-text://{hashlib.sha1(payload.text.encode('utf-8')).hexdigest()[:12]}"
    )
    request_id = build_request_id(source_ref)
    text = payload.text.strip()
    return IngestedSource(
        request_id=request_id,
        source=Source(
            kind="manual_note",
            source_ref=source_ref,
            received_at=payload.received_at,
            sender_name=None,
            sender_organization=None,
            sender_domain=None,
            origin_url=None,
            content_types=["text/plain"],
        ),
        content=Content(
            title=payload.title,
            language=infer_language(f"{payload.title or ''}\n{text}"),
            parts=[
                ContentPart(
                    part_id="title",
                    kind="title",
                    mime_type="text/plain",
                    text_excerpt=payload.title,
                ),
                ContentPart(
                    part_id="body",
                    kind="message",
                    mime_type="text/plain",
                    text_excerpt=text,
                ),
            ],
        ),
        raw_payload=payload.model_dump(),
        extracted_text=_clean_whitespace(text),
    )


def ingest_file(path: str | Path) -> IngestedSource:
    file_path = Path(path).expanduser().resolve()
    if not file_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {file_path}. Check that the path exists relative to {Path.cwd()} and that your test data is present."
        )
    if file_path.suffix.lower() == ".json":
        return ingest_email_json(file_path)
    text = file_path.read_text(encoding="utf-8")
    return ingest_text_payload(
        ExtractionRequest(
            title=file_path.name,
            text=text,
            source_ref=f"file://{file_path}",
        )
    )
