from __future__ import annotations

import json
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

    def test_documents_endpoint_accepts_email_json_upload(self) -> None:
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
                    "/documents",
                    files={"file": (SAMPLE_EMAIL.name, handle, "application/json")},
                )

            self.assertEqual(response.status_code, 201)
            payload = response.json()
            self.assertTrue(payload["stored"])
            self.assertEqual(payload["request_id"], payload["record"]["request_id"])
            self.assertEqual(
                payload["record"]["demand"]["primary_role"]["normalized"],
                "AI Engineer",
            )

            list_response = client.get("/requests")
            self.assertEqual(list_response.status_code, 200)
            self.assertEqual(len(list_response.json()), 1)

    def test_documents_endpoint_accepts_text_upload(self) -> None:
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
                "/documents",
                files={
                    "file": (
                        "request.txt",
                        b"ROLE: Senior Backend Engineer\nLocation: Malmo / hybrid\nKey requirements:\nJava\nAWS",
                        "text/plain",
                    )
                },
            )

            self.assertEqual(response.status_code, 201)
            payload = response.json()
            self.assertTrue(payload["stored"])
            self.assertEqual(
                payload["record"]["demand"]["primary_role"]["normalized"],
                "Backend Engineer",
            )

    def test_documents_endpoint_accepts_eml_upload(self) -> None:
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
            eml_payload = "\n".join(
                [
                    "From: Jane Sender <jane@byteforce.se>",
                    "Date: Tue, 20 May 2025 10:30:00 +0000",
                    "Subject: New Request: Backend Engineer",
                    "Content-Type: text/plain; charset=utf-8",
                    "",
                    "ROLE: Senior Backend Engineer",
                    "Location: Stockholm / hybrid",
                    "Key requirements:",
                    "Java",
                    "AWS",
                ]
            ).encode("utf-8")

            response = client.post(
                "/documents",
                files={"file": ("request.eml", eml_payload, "message/rfc822")},
            )

            self.assertEqual(response.status_code, 201)
            payload = response.json()
            self.assertTrue(payload["stored"])
            self.assertEqual(payload["record"]["source"]["kind"], "email")
            self.assertEqual(payload["record"]["source"]["sender_domain"], "byteforce.se")
            self.assertEqual(
                payload["record"]["demand"]["primary_role"]["normalized"],
                "Backend Engineer",
            )

            list_response = client.get("/requests")
            self.assertEqual(list_response.status_code, 200)
            self.assertEqual(len(list_response.json()), 1)

    def test_documents_endpoint_rejects_unsupported_suffix(self) -> None:
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
                "/documents",
                files={"file": ("request.docx", b"hello", "application/octet-stream")},
            )

            self.assertEqual(response.status_code, 400)

    def test_documents_endpoint_rejects_large_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            app = create_app(
                Settings(
                    database_path=Path(temp_dir) / "db" / "marketpulse.sqlite3",
                    llm_provider="mock",
                    llm_model="mock-extractor-v1",
                    prompt_version="consulting_request_v1_mock",
                    upload_max_bytes=8,
                )
            )
            client = TestClient(app)

            response = client.post(
                "/documents",
                files={"file": ("request.txt", b"this is too large", "text/plain")},
            )

            self.assertEqual(response.status_code, 413)

    def test_demo_email_endpoint_uses_seeded_fallback_without_ai(self) -> None:
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

            first = client.post("/demo/emails", json={"seed": "demo-seed"})
            second = client.post("/demo/emails", json={"seed": "demo-seed"})

            self.assertEqual(first.status_code, 200)
            self.assertEqual(second.status_code, 200)
            payload = first.json()
            self.assertEqual(payload["generated_by"], "fallback")
            self.assertEqual(payload["email"], second.json()["email"])
            self.assertTrue(payload["email"]["id"].startswith("demo-"))
            self.assertIn("from", payload["email"])
            self.assertIn("body", payload["email"])

    def test_demo_email_endpoint_generates_unique_unseeded_fallback(self) -> None:
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

            first = client.post("/demo/emails", json={})
            second = client.post("/demo/emails", json={})

            self.assertEqual(first.status_code, 200)
            self.assertEqual(second.status_code, 200)
            self.assertNotEqual(
                first.json()["email"]["id"],
                second.json()["email"]["id"],
            )

    def test_demo_email_can_be_forwarded_to_documents_and_snapshot(self) -> None:
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

            demo_response = client.post("/demo/emails", json={"seed": "forward-demo"})
            self.assertEqual(demo_response.status_code, 200)
            email = demo_response.json()["email"]
            upload_response = client.post(
                "/documents",
                data={
                    "title": email["subject"],
                    "received_at": email["date"],
                    "source_ref": f"demo-mail://{email['id']}",
                },
                files={
                    "file": (
                        f"{email['id']}.json",
                        json.dumps(email).encode("utf-8"),
                        "application/json",
                    )
                },
            )

            self.assertEqual(upload_response.status_code, 201)
            upload_payload = upload_response.json()
            self.assertTrue(upload_payload["stored"])
            self.assertEqual(upload_payload["record"]["source"]["kind"], "email")
            self.assertIsNotNone(
                upload_payload["record"]["demand"]["primary_role"]["normalized"]
            )

            snapshot_response = client.get("/analytics/snapshot")
            self.assertEqual(snapshot_response.status_code, 200)
            snapshot = snapshot_response.json()
            self.assertEqual(snapshot["row_count"], 1)
            self.assertEqual(len(snapshot["requests"]), 1)
            self.assertEqual(
                snapshot["requests"][0]["request_id"],
                upload_payload["request_id"],
            )
            self.assertIn("sender_domain", snapshot["requests"][0])
            self.assertIn("remote_mode", snapshot["requests"][0])


if __name__ == "__main__":
    unittest.main()
