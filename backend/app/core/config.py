from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BACKEND_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE.exists() else ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Seagulls Communications CRM"
    secret_key: str = "change-me-in-production-seagulls-crm-secret-key-2026"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480
    # PostgreSQL is the primary database. SQLite remains supported for tests only.
    database_url: str = "postgresql+psycopg2://seagulls:seagulls_crm_dev@127.0.0.1:5432/seagulls_crm"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    lead_number_start: int = 1001

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    return Settings()
