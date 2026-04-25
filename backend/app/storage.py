from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from app.contracts import ConsultingRequestV1
from app.models import IndexEntry, StoredRecord


SCHEMA_VERSION = 2


class SQLiteStorage:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _ensure_schema(self) -> None:
        if self.database_path.exists():
            with self._connect() as connection:
                version = connection.execute("PRAGMA user_version").fetchone()[0]
            if version == SCHEMA_VERSION:
                return
            self.database_path.unlink()
        self._initialize()

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                PRAGMA foreign_keys = ON;

                CREATE TABLE IF NOT EXISTS requests (
                    request_id TEXT PRIMARY KEY,
                    received_at TEXT,
                    source_kind TEXT NOT NULL,
                    sender_organization TEXT,
                    sender_domain TEXT,
                    primary_role TEXT,
                    seniority TEXT,
                    sector TEXT,
                    location_city TEXT,
                    remote_mode TEXT,
                    rate_amount INTEGER,
                    rate_currency TEXT,
                    rate_unit TEXT,
                    duration_months INTEGER,
                    review_status TEXT NOT NULL,
                    overall_confidence REAL NOT NULL,
                    stored_at TEXT NOT NULL,
                    record_json TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS request_technologies (
                    request_id TEXT NOT NULL,
                    technology_key TEXT NOT NULL,
                    raw_value TEXT NOT NULL,
                    normalized_value TEXT,
                    category TEXT NOT NULL,
                    importance TEXT,
                    confidence REAL NOT NULL,
                    position INTEGER NOT NULL,
                    PRIMARY KEY (request_id, technology_key),
                    FOREIGN KEY (request_id) REFERENCES requests(request_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS request_languages (
                    request_id TEXT NOT NULL,
                    language_key TEXT NOT NULL,
                    raw_value TEXT NOT NULL,
                    normalized_value TEXT,
                    proficiency TEXT,
                    importance TEXT,
                    confidence REAL NOT NULL,
                    position INTEGER NOT NULL,
                    PRIMARY KEY (request_id, language_key),
                    FOREIGN KEY (request_id) REFERENCES requests(request_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS request_certifications (
                    request_id TEXT NOT NULL,
                    certification_key TEXT NOT NULL,
                    raw_value TEXT,
                    normalized_value TEXT,
                    importance TEXT,
                    confidence REAL NOT NULL,
                    position INTEGER NOT NULL,
                    PRIMARY KEY (request_id, certification_key),
                    FOREIGN KEY (request_id) REFERENCES requests(request_id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_requests_received_at ON requests(received_at);
                CREATE INDEX IF NOT EXISTS idx_requests_primary_role ON requests(primary_role);
                CREATE INDEX IF NOT EXISTS idx_requests_sector ON requests(sector);
                CREATE INDEX IF NOT EXISTS idx_requests_location_city ON requests(location_city);
                CREATE INDEX IF NOT EXISTS idx_requests_review_status ON requests(review_status);
                CREATE INDEX IF NOT EXISTS idx_requests_remote_mode ON requests(remote_mode);
                CREATE INDEX IF NOT EXISTS idx_technologies_normalized_value ON request_technologies(normalized_value);
                CREATE INDEX IF NOT EXISTS idx_technologies_category ON request_technologies(category);
                CREATE INDEX IF NOT EXISTS idx_languages_normalized_value ON request_languages(normalized_value);
                CREATE INDEX IF NOT EXISTS idx_certifications_normalized_value ON request_certifications(normalized_value);

                CREATE VIEW IF NOT EXISTS demand_by_role AS
                SELECT
                    primary_role,
                    COUNT(*) AS request_count,
                    AVG(overall_confidence) AS avg_confidence,
                    MAX(received_at) AS latest_received_at
                FROM requests
                GROUP BY primary_role;

                CREATE VIEW IF NOT EXISTS demand_by_technology AS
                SELECT
                    COALESCE(normalized_value, raw_value) AS technology,
                    category,
                    COUNT(DISTINCT request_id) AS request_count,
                    SUM(CASE WHEN importance = 'required' THEN 1 ELSE 0 END) AS required_count,
                    AVG(confidence) AS avg_confidence
                FROM request_technologies
                GROUP BY COALESCE(normalized_value, raw_value), category;

                CREATE VIEW IF NOT EXISTS demand_by_sector AS
                SELECT
                    sector,
                    COUNT(*) AS request_count,
                    AVG(overall_confidence) AS avg_confidence
                FROM requests
                GROUP BY sector;

                CREATE VIEW IF NOT EXISTS demand_by_city AS
                SELECT
                    location_city,
                    COUNT(*) AS request_count,
                    AVG(overall_confidence) AS avg_confidence
                FROM requests
                GROUP BY location_city;

                CREATE VIEW IF NOT EXISTS demand_monthly AS
                SELECT
                    substr(received_at, 1, 7) AS year_month,
                    primary_role,
                    COUNT(*) AS request_count,
                    AVG(overall_confidence) AS avg_confidence
                FROM requests
                WHERE received_at IS NOT NULL
                GROUP BY substr(received_at, 1, 7), primary_role;
                """
            )
            connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")

    def save(self, record: ConsultingRequestV1) -> StoredRecord:
        stored_at = (
            datetime.now(timezone.utc)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z")
        )
        record_json = json.dumps(record.model_dump(mode="json"), ensure_ascii=False)
        with self._connect() as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute(
                """
                INSERT INTO requests (
                    request_id,
                    received_at,
                    source_kind,
                    sender_organization,
                    sender_domain,
                    primary_role,
                    seniority,
                    sector,
                    location_city,
                    remote_mode,
                    rate_amount,
                    rate_currency,
                    rate_unit,
                    duration_months,
                    review_status,
                    overall_confidence,
                    stored_at,
                    record_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(request_id) DO UPDATE SET
                    received_at = excluded.received_at,
                    source_kind = excluded.source_kind,
                    sender_organization = excluded.sender_organization,
                    sender_domain = excluded.sender_domain,
                    primary_role = excluded.primary_role,
                    seniority = excluded.seniority,
                    sector = excluded.sector,
                    location_city = excluded.location_city,
                    remote_mode = excluded.remote_mode,
                    rate_amount = excluded.rate_amount,
                    rate_currency = excluded.rate_currency,
                    rate_unit = excluded.rate_unit,
                    duration_months = excluded.duration_months,
                    review_status = excluded.review_status,
                    overall_confidence = excluded.overall_confidence,
                    stored_at = excluded.stored_at,
                    record_json = excluded.record_json
                """,
                (
                    record.request_id,
                    record.source.received_at,
                    record.source.kind,
                    record.source.sender_organization,
                    record.source.sender_domain,
                    record.demand.primary_role.normalized,
                    record.demand.seniority.normalized,
                    record.demand.sector.normalized,
                    record.demand.location.city,
                    record.demand.remote_mode.normalized,
                    record.demand.commercial.rate_amount,
                    record.demand.commercial.rate_currency,
                    record.demand.commercial.rate_unit,
                    record.demand.commercial.duration_months,
                    record.quality.review_status,
                    record.quality.overall_confidence,
                    stored_at,
                    record_json,
                ),
            )
            connection.execute(
                "DELETE FROM request_technologies WHERE request_id = ?",
                (record.request_id,),
            )
            connection.execute(
                "DELETE FROM request_languages WHERE request_id = ?",
                (record.request_id,),
            )
            connection.execute(
                "DELETE FROM request_certifications WHERE request_id = ?",
                (record.request_id,),
            )
            self._insert_technologies(connection, record)
            self._insert_languages(connection, record)
            self._insert_certifications(connection, record)
        return StoredRecord(record=record, database_path=self.database_path)

    def _insert_technologies(
        self, connection: sqlite3.Connection, record: ConsultingRequestV1
    ) -> None:
        rows = []
        for position, technology in enumerate(record.demand.technologies):
            key = technology.normalized or technology.raw
            rows.append(
                (
                    record.request_id,
                    key,
                    technology.raw,
                    technology.normalized,
                    technology.category,
                    technology.importance,
                    technology.confidence,
                    position,
                )
            )
        if rows:
            connection.executemany(
                """
                INSERT INTO request_technologies (
                    request_id,
                    technology_key,
                    raw_value,
                    normalized_value,
                    category,
                    importance,
                    confidence,
                    position
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )

    def _insert_languages(
        self, connection: sqlite3.Connection, record: ConsultingRequestV1
    ) -> None:
        rows = []
        for position, language in enumerate(record.demand.languages):
            key = language.normalized or language.raw
            rows.append(
                (
                    record.request_id,
                    key,
                    language.raw,
                    language.normalized,
                    language.proficiency,
                    language.importance,
                    language.confidence,
                    position,
                )
            )
        if rows:
            connection.executemany(
                """
                INSERT INTO request_languages (
                    request_id,
                    language_key,
                    raw_value,
                    normalized_value,
                    proficiency,
                    importance,
                    confidence,
                    position
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )

    def _insert_certifications(
        self, connection: sqlite3.Connection, record: ConsultingRequestV1
    ) -> None:
        rows = []
        for position, certification in enumerate(record.demand.certifications):
            key = certification.normalized or certification.raw or f"cert-{position}"
            rows.append(
                (
                    record.request_id,
                    key,
                    certification.raw,
                    certification.normalized,
                    certification.importance,
                    certification.confidence,
                    position,
                )
            )
        if rows:
            connection.executemany(
                """
                INSERT INTO request_certifications (
                    request_id,
                    certification_key,
                    raw_value,
                    normalized_value,
                    importance,
                    confidence,
                    position
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )

    def list_requests(self) -> list[IndexEntry]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT request_id, received_at, source_kind, primary_role, sector,
                       location_city, review_status, overall_confidence, stored_at
                FROM requests
                ORDER BY received_at DESC, stored_at DESC
                """
            ).fetchall()
        return [IndexEntry.model_validate(dict(row)) for row in rows]

    def list_request_snapshot_rows(self) -> list[dict]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    request_id,
                    received_at,
                    source_kind,
                    sender_organization,
                    sender_domain,
                    primary_role,
                    seniority,
                    sector,
                    location_city,
                    remote_mode,
                    rate_amount,
                    rate_currency,
                    rate_unit,
                    duration_months,
                    review_status,
                    overall_confidence
                FROM requests
                ORDER BY received_at ASC, request_id ASC
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def get_request(self, request_id: str) -> ConsultingRequestV1:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT record_json FROM requests WHERE request_id = ?",
                (request_id,),
            ).fetchone()
        if row is None:
            raise FileNotFoundError(request_id)
        payload = json.loads(row["record_json"])
        return ConsultingRequestV1.model_validate(payload)
