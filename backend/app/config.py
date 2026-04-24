from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MARKET_PULSE_", extra="ignore")

    app_name: str = "Market Pulse Backend"
    llm_provider: str = "mock"
    llm_model: str = "mock-extractor-v1"
    prompt_version: str = "consulting_request_v1_mock"
    storage_root: Path = REPO_ROOT / "data"

    @field_validator("storage_root", mode="before")
    @classmethod
    def expand_storage_root(cls, value: str | Path) -> Path:
        return Path(value).expanduser().resolve()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
