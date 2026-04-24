from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from app.api import create_app
from app.chat import ReadOnlySqlRunner, UnsafeQueryError, validate_readonly_sql
from app.config import Settings


class ChatSqlTests(unittest.TestCase):
    def test_validate_readonly_sql_accepts_select_and_with(self) -> None:
        self.assertEqual(validate_readonly_sql("SELECT 1;"), "SELECT 1")
        self.assertEqual(
            validate_readonly_sql("WITH sample AS (SELECT 1) SELECT * FROM sample"),
            "WITH sample AS (SELECT 1) SELECT * FROM sample",
        )

    def test_validate_readonly_sql_rejects_writes_and_multi_statements(self) -> None:
        blocked_queries = [
            "DELETE FROM requests",
            "UPDATE requests SET sector = 'public'",
            "DROP TABLE requests",
            "PRAGMA table_info(requests)",
            "ATTACH DATABASE 'x' AS other",
            "SELECT 1; SELECT 2",
        ]
        for query in blocked_queries:
            with self.subTest(query=query):
                with self.assertRaises(UnsafeQueryError):
                    validate_readonly_sql(query)

    def test_runner_limits_rows(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "marketpulse.sqlite3"
            with sqlite3.connect(database_path) as connection:
                connection.execute("CREATE TABLE sample (value INTEGER)")
                connection.executemany(
                    "INSERT INTO sample (value) VALUES (?)",
                    [(1,), (2,), (3,)],
                )

            runner = ReadOnlySqlRunner(database_path, max_rows=2)
            result = runner.run("SELECT value FROM sample ORDER BY value")

            self.assertEqual(result.row_count, 2)
            self.assertEqual(result.rows, [{"value": 1}, {"value": 2}])


class ChatApiTests(unittest.TestCase):
    def test_chat_endpoint_answers_dotnet_2025_question(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "marketpulse.sqlite3"
            app = create_app(
                Settings(
                    database_path=database_path,
                    llm_provider="mock",
                    llm_model="mock-extractor-v1",
                    prompt_version="consulting_request_v1_mock",
                )
            )
            with sqlite3.connect(database_path) as connection:
                connection.execute(
                    """
                    INSERT INTO requests (
                        request_id, received_at, source_kind, primary_role,
                        review_status, overall_confidence, stored_at, record_json
                    ) VALUES
                        ('req-1', '2025-02-01T09:00:00+00:00', 'email', '.NET Developer', 'ok', 0.9, '2025-02-01T09:00:00Z', '{}'),
                        ('req-2', '2025-03-01T09:00:00+00:00', 'email', 'Backend Engineer', 'ok', 0.9, '2025-03-01T09:00:00Z', '{}'),
                        ('req-3', '2024-03-01T09:00:00+00:00', 'email', '.NET Developer', 'ok', 0.9, '2024-03-01T09:00:00Z', '{}')
                    """
                )
                connection.execute(
                    """
                    INSERT INTO request_technologies (
                        request_id, technology_key, raw_value, normalized_value,
                        category, importance, confidence, position
                    ) VALUES
                        ('req-2', '.NET', '.NET', '.NET', 'framework', 'required', 0.9, 0)
                    """
                )
            client = TestClient(app)

            response = client.post(
                "/chat",
                json={
                    "message": "hur många förfrågningar om .net utvecklare inkom under 2025?"
                },
            )

            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertIn("2", payload["answer"])
            self.assertEqual(payload["rows"][0]["request_count"], 2)
            self.assertTrue(payload["sql"])


if __name__ == "__main__":
    unittest.main()
