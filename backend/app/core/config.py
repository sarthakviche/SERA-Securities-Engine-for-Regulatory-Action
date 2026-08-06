"""Application settings, loaded from environment variables / .env.

Per TRD §17 (Environment & Configuration Reference). Only the subset needed
by the impact_mapping / sop_generation / evidence_implementation_plan slice
is populated here; DATABASE_URL, REDIS_URL, S3_*, JWT_* etc. are left for
whoever wires up the corresponding infra (core/db.py, auth, workers).
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-5"

    # Backend selector for this slice's swappable fakes (see ai/graph/deps.py).
    # "memory" (default, prototype) -> in-memory fakes.
    # "postgres" -> real implementations; not wired up yet, reserved for teammates.
    org_data_backend: str = "memory"


@lru_cache
def get_settings() -> Settings:
    return Settings()
