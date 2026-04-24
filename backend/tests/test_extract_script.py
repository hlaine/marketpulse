from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from app.config import get_settings
from scripts.extract import main


REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_EMAIL = (
    REPO_ROOT / "data" / "emails" / "0003_Ny förfrågan  brådskande Backend Enginee.json"
)


class ExtractScriptTests(unittest.TestCase):
    def tearDown(self) -> None:
        get_settings.cache_clear()

    def test_main_prints_summary_output_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = io.StringIO()
            get_settings.cache_clear()
            with (
                patch(
                    "sys.argv",
                    [
                        "extract.py",
                        str(SAMPLE_EMAIL),
                    ],
                ),
                patch.dict(
                    "os.environ",
                    {
                        "MARKET_PULSE_DATABASE_PATH": str(
                            Path(temp_dir) / "db" / "test.sqlite3"
                        ),
                        "MARKET_PULSE_LLM_PROVIDER": "mock",
                        "MARKET_PULSE_LLM_MODEL": "mock-extractor-v1",
                        "MARKET_PULSE_PROMPT_VERSION": "consulting_request_v1_mock",
                    },
                    clear=False,
                ),
                redirect_stdout(output),
            ):
                exit_code = main()

        rendered = output.getvalue()
        self.assertEqual(exit_code, 0)
        self.assertIn("OK     req-0003", rendered)
        self.assertIn("Backend Engineer", rendered)
        self.assertIn("Tokens: n/a", rendered)

    def test_main_supports_json_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = io.StringIO()
            get_settings.cache_clear()
            with (
                patch(
                    "sys.argv",
                    ["extract.py", "--json", str(SAMPLE_EMAIL)],
                ),
                patch.dict(
                    "os.environ",
                    {
                        "MARKET_PULSE_DATABASE_PATH": str(
                            Path(temp_dir) / "db" / "test.sqlite3"
                        ),
                        "MARKET_PULSE_LLM_PROVIDER": "mock",
                        "MARKET_PULSE_LLM_MODEL": "mock-extractor-v1",
                        "MARKET_PULSE_PROMPT_VERSION": "consulting_request_v1_mock",
                    },
                    clear=False,
                ),
                redirect_stdout(output),
            ):
                exit_code = main()

        rendered = output.getvalue()
        self.assertEqual(exit_code, 0)
        self.assertIn('"request_id": "req-0003"', rendered)
        self.assertIn('"primary_role"', rendered)

    def test_main_accepts_directory_input_for_batch_runs(self) -> None:
        emails_dir = SAMPLE_EMAIL.parent
        with tempfile.TemporaryDirectory() as temp_dir:
            output = io.StringIO()
            get_settings.cache_clear()
            with (
                patch(
                    "sys.argv",
                    ["extract.py", str(emails_dir)],
                ),
                patch.dict(
                    "os.environ",
                    {
                        "MARKET_PULSE_DATABASE_PATH": str(
                            Path(temp_dir) / "db" / "test.sqlite3"
                        ),
                        "MARKET_PULSE_LLM_PROVIDER": "mock",
                        "MARKET_PULSE_LLM_MODEL": "mock-extractor-v1",
                        "MARKET_PULSE_PROMPT_VERSION": "consulting_request_v1_mock",
                    },
                    clear=False,
                ),
                redirect_stdout(output),
            ):
                exit_code = main()

        rendered = output.getvalue()
        self.assertEqual(exit_code, 0)
        self.assertIn("req-0003", rendered)
        self.assertIn("Done:", rendered)


if __name__ == "__main__":
    unittest.main()
