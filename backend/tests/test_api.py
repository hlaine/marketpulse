from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from app.api import create_app
from app.config import Settings


REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_EMAIL = (
    REPO_ROOT / "data" / "emails" / "0177_ASAP AI Engineer  AIML  Fintech.json"
)


class ApiTests(unittest.TestCase):
    def test_extract_endpoint_accepts_email_json_upload(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            app = create_app(
                Settings(
                    database_path=Path(temp_dir) / "db" / "marketpulse.sqlite3",
                    llm_provider="mock",
                    llm_model="mock-extractor-v1",
                    prompt_version="consulting_request_v1_mock",
                )
            )
            client = TestClient(app)

            with SAMPLE_EMAIL.open("rb") as handle:
                response = client.post(
                    "/extract",
                    files={"file": (SAMPLE_EMAIL.name, handle, "application/json")},
                )

            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertEqual(
                payload["demand"]["primary_role"]["normalized"], "AI Engineer"
            )
            self.assertEqual(payload["demand"]["location"]["city"], "Göteborg")
            self.assertEqual(payload["demand"]["remote_mode"]["normalized"], "remote")

            list_response = client.get("/requests")
            self.assertEqual(list_response.status_code, 200)
            self.assertEqual(len(list_response.json()), 1)

    def test_extract_endpoint_accepts_json_payload(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            app = create_app(
                Settings(
                    database_path=Path(temp_dir) / "db" / "marketpulse.sqlite3",
                    llm_provider="mock",
                    llm_model="mock-extractor-v1",
                    prompt_version="consulting_request_v1_mock",
                )
            )
            client = TestClient(app)

            response = client.post(
                "/extract",
                json={
                    "title": "New Request: Backend Engineer",
                    "text": "Client: Riksdata\nROLE: Senior Backend Engineer\nStart: ASAP\nDuration: 6 months\nLocation: Malmö / hybrid\nRate: 950 SEK/h\nKey requirements:\n• Java\n• AWS\n• Docker",
                },
            )

            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertEqual(
                payload["demand"]["primary_role"]["normalized"], "Backend Engineer"
            )
            self.assertEqual(payload["demand"]["remote_mode"]["normalized"], "hybrid")


if __name__ == "__main__":
    unittest.main()
