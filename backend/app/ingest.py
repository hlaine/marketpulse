from __future__ import annotations

import hashlib
import html
import json
import re
from email import policy
from email.parser import BytesParser
from email.utils import parseaddr
from pathlib import Path

from pypdf import PdfReader

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


def _looks_like_email_payload(payload: dict) -> bool:
    return any(key in payload for key in ["body", "subject", "from", "date"])


def _apply_file_metadata(
    source: IngestedSource,
    title: str | None = None,
    received_at: str | None = None,
    source_ref: str | None = None,
) -> IngestedSource:
    if title:
        source.content.title = title
        if source.content.parts:
            title_part = next(
                (part for part in source.content.parts if part.part_id == "title"),
                None,
            )
            if title_part is not None:
                title_part.text_excerpt = title
    if received_at:
        source.source.received_at = received_at
    if source_ref:
        source.source.source_ref = source_ref
        source.request_id = build_request_id(source_ref)
    return source


def ingest_text_payload(
    payload: ExtractionRequest,
    source_kind: str = "manual_note",
    content_types: list[str] | None = None,
    body_part_kind: str = "message",
) -> IngestedSource:
    source_ref = (
        payload.source_ref
        or f"manual-text://{hashlib.sha1(payload.text.encode('utf-8')).hexdigest()[:12]}"
    )
    request_id = build_request_id(source_ref)
    text = payload.text.strip()
    return IngestedSource(
        request_id=request_id,
        source=Source(
            kind=source_kind,
            source_ref=source_ref,
            received_at=payload.received_at,
            sender_name=None,
            sender_organization=None,
            sender_domain=None,
            origin_url=None,
            content_types=content_types or ["text/plain"],
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
                    kind=body_part_kind,
                    mime_type=(content_types or ["text/plain"])[0],
                    text_excerpt=text,
                ),
            ],
        ),
        raw_payload=payload.model_dump(),
        extracted_text=_clean_whitespace(text),
    )


def _read_pdf_text(path: Path) -> str:
    reader = PdfReader(str(path))
    page_texts = [page.extract_text() or "" for page in reader.pages]
    return "\n\n".join(text.strip() for text in page_texts if text.strip()).strip()


def _decode_email_part(part) -> str:
    payload = part.get_payload(decode=True)
    charset = part.get_content_charset() or "utf-8"
    if payload is None:
        raw = part.get_payload()
        return raw if isinstance(raw, str) else ""
    return payload.decode(charset, errors="replace")


def _extract_eml_body(message) -> tuple[str, str]:
    plain_parts: list[str] = []
    html_parts: list[str] = []
    parts = message.walk() if message.is_multipart() else [message]
    for part in parts:
        if part.is_multipart():
            continue
        disposition = part.get_content_disposition()
        if disposition == "attachment":
            continue
        content_type = part.get_content_type()
        if content_type == "text/plain":
            plain_parts.append(_decode_email_part(part))
        elif content_type == "text/html":
            html_parts.append(strip_html(_decode_email_part(part)))
    if plain_parts:
        return "\n\n".join(part.strip() for part in plain_parts if part.strip()), "text/plain"
    if html_parts:
        return "\n\n".join(part.strip() for part in html_parts if part.strip()), "text/html"
    return "", "message/rfc822"


def ingest_eml_file(
    path: Path,
    title: str | None = None,
    received_at: str | None = None,
    source_ref: str | None = None,
) -> IngestedSource:
    message = BytesParser(policy=policy.default).parsebytes(path.read_bytes())
    header_subject = str(message.get("subject") or "").strip() or None
    header_date = str(message.get("date") or "").strip() or None
    header_from = str(message.get("from") or "").strip() or None
    sender_name, sender_organization, sender_domain = parse_sender(header_from)
    body_text, body_mime_type = _extract_eml_body(message)
    resolved_title = title or header_subject
    resolved_received_at = received_at or header_date
    resolved_source_ref = source_ref or f"eml://{path.name}"
    combined = "\n\n".join(
        part for part in [resolved_title or "", body_text] if part
    ).strip()
    return IngestedSource(
        request_id=build_request_id(resolved_source_ref),
        source=Source(
            kind="email",
            source_ref=resolved_source_ref,
            received_at=resolved_received_at,
            sender_name=sender_name,
            sender_organization=sender_organization,
            sender_domain=sender_domain,
            origin_url=None,
            content_types=["message/rfc822", body_mime_type],
        ),
        content=Content(
            title=resolved_title,
            language=infer_language(combined),
            parts=[
                ContentPart(
                    part_id="title",
                    kind="title",
                    mime_type="text/plain",
                    text_excerpt=resolved_title,
                ),
                ContentPart(
                    part_id="body",
                    kind="message",
                    mime_type=body_mime_type,
                    text_excerpt=body_text,
                ),
            ],
        ),
        raw_payload={
            "subject": header_subject,
            "date": header_date,
            "from": header_from,
        },
        extracted_text=_clean_whitespace(combined),
        input_path=path,
    )


def ingest_file(
    path: str | Path,
    title: str | None = None,
    received_at: str | None = None,
    source_ref: str | None = None,
) -> IngestedSource:
    file_path = Path(path).expanduser().resolve()
    if not file_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {file_path}. Check that the path exists relative to {Path.cwd()} and that your test data is present."
        )
    suffix = file_path.suffix.lower()
    effective_source_ref = source_ref or f"file://{file_path}"
    if suffix == ".json":
        payload = json.loads(file_path.read_text(encoding="utf-8"))
        if isinstance(payload, dict) and _looks_like_email_payload(payload):
            return _apply_file_metadata(
                ingest_email_json(file_path),
                title=title,
                received_at=received_at,
                source_ref=source_ref,
            )
        text = json.dumps(payload, ensure_ascii=False, indent=2)
        return ingest_text_payload(
            ExtractionRequest(
                title=title or file_path.name,
                text=text,
                source_ref=effective_source_ref,
                received_at=received_at,
            ),
            source_kind="document",
            content_types=["application/json"],
            body_part_kind="document",
        )
    if suffix == ".pdf":
        text = _read_pdf_text(file_path)
        return ingest_text_payload(
            ExtractionRequest(
                title=title or file_path.name,
                text=text,
                source_ref=effective_source_ref,
                received_at=received_at,
            ),
            source_kind="document",
            content_types=["application/pdf"],
            body_part_kind="document",
        )
    if suffix == ".eml":
        return ingest_eml_file(
            file_path,
            title=title,
            received_at=received_at,
            source_ref=source_ref,
        )
    text = file_path.read_text(encoding="utf-8")
    content_type = {
        ".md": "text/markdown",
    }.get(suffix, "text/plain")
    return ingest_text_payload(
        ExtractionRequest(
            title=title or file_path.name,
            text=text,
            source_ref=effective_source_ref,
            received_at=received_at,
        ),
        source_kind="document",
        content_types=[content_type],
        body_part_kind="document",
    )
