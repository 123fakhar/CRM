from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BACKEND_DIR / ".env"


def normalize_database_url(url: str) -> str:
    """Normalize provider URLs (Railway/Heroku) for SQLAlchemy + psycopg2."""
    if not url:
        return url
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    if url.startswith("postgresql://") and "+psycopg2" not in url and "+psycopg" not in url:
        url = "postgresql+psycopg2://" + url[len("postgresql://") :]

    # Public Railway proxy hosts need SSL. Private *.railway.internal usually does not
    # and can fail healthchecks if sslmode=require is forced.
    public_markers = ("rlwy.net", "railway.app", "proxy.rlwy.net")
    is_public = any(marker in url for marker in public_markers)
    is_private = "railway.internal" in url
    if is_public and not is_private and "sslmode=" not in url:
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}sslmode=require"
    return url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE.exists() else ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    app_name: str = "Seagulls Communications CRM"
    secret_key: str = "change-me-in-production-seagulls-crm-secret-key-2026"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480
    # Prefer development unless Railway/dashboard explicitly sets production.
    # (Avoid baking production into the image so local/default URL checks stay sane.)
    environment: str = "development"
    # Accept common Railway Postgres variable names.
    database_url: str = Field(
        default="postgresql+psycopg2://seagulls:seagulls_crm_dev@127.0.0.1:5432/seagulls_crm",
        validation_alias=AliasChoices(
            "DATABASE_URL",
            "POSTGRES_URL",
            "POSTGRES_PRIVATE_URL",
            "DATABASE_PRIVATE_URL",
            "DATABASE_PUBLIC_URL",
        ),
    )
    # Comma-separated browser origins. Empty = same-origin SPA only (recommended on Railway).
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    lead_number_start: int = 1001
    static_dir: str = str(BACKEND_DIR / "static")
    # Production-only first admin (never commit real values)
    bootstrap_admin_email: str | None = None
    bootstrap_admin_password: str | None = None
    bootstrap_admin_name: str = "System Admin"
    port: int = Field(default=8000, validation_alias=AliasChoices("PORT", "port"))

    @field_validator("database_url", mode="before")
    @classmethod
    def _coerce_database_url(cls, value: Any) -> Any:
        if value is None:
            return value
        return str(value).strip()

    @model_validator(mode="after")
    def _validate_production_database(self) -> "Settings":
        # Do not crash process import on Railway — runtime DB init reports errors
        # via /api/health while /health stays up for platform probes.
        if self.environment.lower() == "production":
            url = self.database_url.lower()
            if "127.0.0.1" in url or "localhost" in url:
                import logging

                logging.getLogger("uvicorn.error").error(
                    "DATABASE_URL still points at localhost in production. "
                    "Link Railway PostgreSQL to this service."
                )
        return self

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
