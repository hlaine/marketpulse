from __future__ import annotations

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


class PipelineTests(unittest.TestCase):
    def test_ingest_email_json_extracts_expected_fields(self) -> None:
        ingested = ingest_file(SAMPLE_EMAIL)
        self.assertEqual(ingested.request_id, "req-0003")
        self.assertEqual(ingested.source.kind, "email")
        self.assertEqual(ingested.content.language, "sv")
        self.assertIn("Backend Engineer", ingested.extracted_text)

    def test_pipeline_processes_email_json_and_persists_record(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings(storage_root=Path(temp_dir))
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
            self.assertTrue((Path(temp_dir) / "requests" / "req-0003.json").exists())


if __name__ == "__main__":
    unittest.main()
