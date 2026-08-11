from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BACKEND_DIR / ".env"


def normalize_database_url(url: str) -> str:
    """Normalize provider URLs (Railway/Heroku) for SQLAlchemy + psycopg2."""
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    if url.startswith("postgresql://") and "+psycopg2" not in url and "+psycopg" not in url:
        url = "postgresql+psycopg2://" + url[len("postgresql://") :]
    return url


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
    # development | production
    environment: str = "development"
    # PostgreSQL is the primary database. SQLite remains supported for tests only.
    database_url: str = "postgresql+psycopg2://seagulls:seagulls_crm_dev@127.0.0.1:5432/seagulls_crm"
    # Comma-separated browser origins. Empty = same-origin SPA only (recommended on Railway).
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    lead_number_start: int = 1001
    static_dir: str = str(BACKEND_DIR / "static")
    # Production-only first admin (never commit real values)
    bootstrap_admin_email: str | None = None
    bootstrap_admin_password: str | None = None
    bootstrap_admin_name: str = "System Admin"

    @property
    def sqlalchemy_database_url(self) -> str:
        return normalize_database_url(self.database_url)

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_sqlite(self) -> bool:
        return self.sqlalchemy_database_url.startswith("sqlite")

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
