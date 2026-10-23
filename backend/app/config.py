"""Runtime configuration loaded from environment variables or backend/.env."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ai_provider: Literal["anthropic", "gemini"] = "anthropic"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-flash-lite-latest"
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-opus-5-5"
    allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    rate_limit_per_minute: int = 10
    audit_log_path: str = "logs/audit.jsonl"
    # Upper bound on agent turns so a misbehaving model cannot loop forever.
    max_agent_turns: int = 6
    # Total time budget for one assessment; the frontend aborts at 60 seconds.
    request_deadline_seconds: float = 55.0

    @property
    def configured_api_key(self) -> str | None:
        return self.gemini_api_key if self.ai_provider == "gemini" else self.anthropic_api_key

    @property
    def origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
