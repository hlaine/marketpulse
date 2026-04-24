from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from app.config import Settings
from app.ingest import ingest_file
from app.pipeline import ExtractionPipeline


REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_EMAIL = (
    REPO_ROOT / "data" / "emails" / "0003_Ny förfrågan  brådskande Backend Enginee.json"
)
SECOND_EMAIL = (
    REPO_ROOT / "data" / "emails" / "0177_ASAP AI Engineer  AIML  Fintech.json"
)


class PipelineTests(unittest.TestCase):
    def test_ingest_email_json_extracts_expected_fields(self) -> None:
        ingested = ingest_file(SAMPLE_EMAIL)
        self.assertEqual(ingested.request_id, "req-0003")
        self.assertEqual(ingested.source.kind, "email")
        self.assertEqual(ingested.content.language, "sv")
        self.assertIn("Backend Engineer", ingested.extracted_text)

    def test_pipeline_processes_email_json_and_persists_record(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "db" / "marketpulse.sqlite3"
            settings = Settings(database_path=database_path)
            pipeline = ExtractionPipeline(settings)
            result = pipeline.process_file(SAMPLE_EMAIL)

            self.assertEqual(result.request_id, "req-0003")
            self.assertEqual(result.demand.primary_role.normalized, "Backend Engineer")
            self.assertEqual(result.demand.seniority.normalized, "senior")
            self.assertEqual(result.demand.sector.normalized, "private")
            self.assertEqual(result.demand.location.city, "Stockholm")
            self.assertEqual(result.demand.remote_mode.normalized, "onsite")
            self.assertEqual(result.demand.commercial.duration_months, 6)
            self.assertEqual(result.demand.commercial.rate_amount, 850)
            self.assertTrue(database_path.exists())

            with sqlite3.connect(database_path) as connection:
                row = connection.execute(
                    "SELECT primary_role, sector FROM requests WHERE request_id = ?",
                    ("req-0003",),
                ).fetchone()

            self.assertIsNotNone(row)
            self.assertEqual(row[0], "Backend Engineer")
            self.assertEqual(row[1], "private")

    def test_pipeline_populates_technology_table_and_aggregate_views(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "db" / "marketpulse.sqlite3"
            settings = Settings(database_path=database_path)
            pipeline = ExtractionPipeline(settings)
            pipeline.process_file(SAMPLE_EMAIL)
            pipeline.process_file(SECOND_EMAIL)

            with sqlite3.connect(database_path) as connection:
                technology_rows = connection.execute(
                    """
                    SELECT normalized_value, category
                    FROM request_technologies
                    WHERE request_id = ?
                    ORDER BY position
                    """,
                    ("req-0003",),
                ).fetchall()
                role_summary = connection.execute(
                    "SELECT request_count FROM demand_by_role WHERE primary_role = ?",
                    ("Backend Engineer",),
                ).fetchone()
                aws_summary = connection.execute(
                    "SELECT request_count FROM demand_by_technology WHERE technology = ?",
                    ("AWS",),
                ).fetchone()
                month_summary = connection.execute(
                    "SELECT request_count FROM demand_monthly WHERE year_month = ? AND primary_role = ?",
                    ("2025-04", "AI Engineer"),
                ).fetchone()

            self.assertEqual(
                [(row[0], row[1]) for row in technology_rows],
                [("Docker", "tool"), ("AWS", "cloud"), ("Java", "language")],
            )
            self.assertEqual(role_summary[0], 1)
            self.assertEqual(aws_summary[0], 2)
            self.assertEqual(month_summary[0], 1)


if __name__ == "__main__":
    unittest.main()
