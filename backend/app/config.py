from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="MARKET_PULSE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Market Pulse Backend"
    llm_provider: str = "mock"
    llm_model: str = "mock-extractor-v1"
    llm_base_url: str | None = None
    llm_api_key: str | None = None
    llm_timeout_seconds: float = 30.0
    prompt_version: str = "consulting_request_v1_mock"
    database_path: Path = REPO_ROOT / "db" / "marketpulse.sqlite3"

    @field_validator("database_path", mode="before")
    @classmethod
    def expand_database_path(cls, value: str | Path) -> Path:
        return Path(value).expanduser().resolve()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
