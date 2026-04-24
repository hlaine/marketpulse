from __future__ import annotations

import json
import unittest

import httpx

from app.config import Settings
from app.ingest import ingest_text_payload
from app.llm import (
    MockExtractorProvider,
    OpenAICompatibleExtractorProvider,
    ProviderError,
    build_extractor_provider,
)
from app.models import ExtractionRequest


class LlmTests(unittest.TestCase):
    def test_build_extractor_provider_returns_mock_provider(self) -> None:
        provider = build_extractor_provider(
            Settings(
                llm_provider="mock",
                llm_model="mock-extractor-v1",
                prompt_version="consulting_request_v1_mock",
            )
        )
        self.assertIsInstance(provider, MockExtractorProvider)

    def test_build_extractor_provider_requires_openai_config(self) -> None:
        with self.assertRaises(ProviderError):
            build_extractor_provider(
                Settings(
                    llm_provider="openai_compatible",
                    llm_model="gpt-5.4",
                    llm_base_url=None,
                    llm_api_key=None,
                )
            )

    def test_openai_provider_parses_valid_json_response(self) -> None:
        source = ingest_text_payload(
            ExtractionRequest(
                title="New Request: Backend Engineer",
                text="ROLE: Senior Backend Engineer\nLocation: Malmö / hybrid\nRate: 950 SEK/h",
            )
        )

        response_payload = {
            "usage": {
                "prompt_tokens": 321,
                "completion_tokens": 123,
                "total_tokens": 444,
            },
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "demand": {
                                    "primary_role": {
                                        "raw": "Backend Engineer",
                                        "normalized": "Backend Engineer",
                                        "confidence": 0.94,
                                        "evidence": [],
                                    },
                                    "secondary_roles": [],
                                    "seniority": {
                                        "raw": "Senior",
                                        "normalized": "senior",
                                        "confidence": 0.91,
                                        "evidence": [],
                                    },
                                    "technologies": [],
                                    "certifications": [],
                                    "languages": [],
                                    "sector": {
                                        "raw": None,
                                        "normalized": "unknown",
                                        "confidence": 0.3,
                                        "evidence": [],
                                    },
                                    "location": {
                                        "raw": "Malmö / hybrid",
                                        "city": "Malmö",
                                        "country": "Sweden",
                                        "confidence": 0.92,
                                        "evidence": [],
                                    },
                                    "remote_mode": {
                                        "raw": "Malmö / hybrid",
                                        "normalized": "hybrid",
                                        "confidence": 0.92,
                                        "evidence": [],
                                    },
                                    "commercial": {
                                        "start_date": None,
                                        "start_date_raw": None,
                                        "duration_raw": None,
                                        "duration_months": None,
                                        "allocation_percent": None,
                                        "positions_count": 1,
                                        "rate_amount": 950,
                                        "rate_currency": "SEK",
                                        "rate_unit": "hour",
                                        "confidence": 0.8,
                                        "evidence": [],
                                    },
                                    "summary": {
                                        "text": "Request for a Backend Engineer in Malmö.",
                                        "confidence": 0.88,
                                    },
                                },
                                "quality": {
                                    "overall_confidence": 0.86,
                                    "review_status": "ok",
                                    "warnings": [],
                                },
                            }
                        )
                    }
                }
            ],
        }

        transport = httpx.MockTransport(
            lambda request: httpx.Response(200, json=response_payload)
        )
        client = httpx.Client(transport=transport)
        provider = OpenAICompatibleExtractorProvider(
            base_url="https://api.openai.com/v1",
            api_key="test-key",
            model_name="gpt-5.4",
            prompt_version="consulting_request_v1",
            http_client=client,
        )

        result = provider.extract_structured_request(source)

        self.assertEqual(result.record.request_id, source.request_id)
        self.assertEqual(
            result.record.demand.primary_role.normalized, "Backend Engineer"
        )
        self.assertEqual(result.record.demand.location.city, "Malmö")
        self.assertEqual(result.record.processing.extractor_model, "gpt-5.4")
        self.assertIsNotNone(result.usage)
        assert result.usage is not None
        self.assertEqual(result.usage.input_tokens, 321)
        self.assertEqual(result.usage.output_tokens, 123)
        self.assertEqual(result.usage.total_tokens, 444)

    def test_openai_provider_rejects_invalid_json_response(self) -> None:
        source = ingest_text_payload(ExtractionRequest(text="ROLE: Backend Engineer"))
        response_payload = {"choices": [{"message": {"content": "not-json"}}]}
        transport = httpx.MockTransport(
            lambda request: httpx.Response(200, json=response_payload)
        )
        client = httpx.Client(transport=transport)
        provider = OpenAICompatibleExtractorProvider(
            base_url="https://api.openai.com/v1",
            api_key="test-key",
            model_name="gpt-5.4",
            prompt_version="consulting_request_v1",
            http_client=client,
        )

        with self.assertRaises(ProviderError):
            provider.extract_structured_request(source)


if __name__ == "__main__":
    unittest.main()
