from contextlib import asynccontextmanager, suppress
from pathlib import Path
import asyncio
import logging
import os
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.core.config import get_settings
from app.core.database import Base, SessionLocal, engine
import app.models  # noqa: F401 — register ORM metadata before create_all
from app.routes import (
    agents,
    audit,
    auth,
    campaigns,
    closers,
    leads,
    reports,
    settings as settings_routes,
    users,
)
from app.seed import seed_if_empty

logger = logging.getLogger("uvicorn.error")
settings = get_settings()
STATIC_DIR = Path(settings.static_dir)
_db_ready = False
_db_error: str | None = None


def _init_database_sync(max_attempts: int = 30, delay_seconds: float = 2.0) -> None:
    """Wait for Postgres, create schema, then optional bootstrap/seed."""
    global _db_ready, _db_error
    last_error: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            Base.metadata.create_all(bind=engine)
            db = SessionLocal()
            try:
                seed_if_empty(db)
            finally:
                db.close()
            _db_ready = True
            _db_error = None
            logger.info("Database ready (attempt %s/%s)", attempt, max_attempts)
            return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            _db_error = str(exc)
            logger.warning(
                "Database not ready (attempt %s/%s): %s",
                attempt,
                max_attempts,
                exc,
            )
            time.sleep(delay_seconds)
    _db_ready = False
    _db_error = f"Database initialization failed after {max_attempts} attempts: {last_error}"
    logger.error(_db_error)


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info(
        "Starting %s env=%s port=%s has_database_url=%s static_dir=%s",
        settings.app_name,
        settings.environment,
        os.getenv("PORT", "8000"),
        bool(os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")),
        STATIC_DIR,
    )
    # Serve immediately so Railway liveness checks succeed while DB connects.
    task = asyncio.create_task(asyncio.to_thread(_init_database_sync))
    try:
        yield
    finally:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)

cors_origins = settings.cors_origin_list
if cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(agents.router)
app.include_router(closers.router)
app.include_router(campaigns.router)
app.include_router(leads.router)
app.include_router(reports.router)
app.include_router(audit.router)
app.include_router(settings_routes.router)


@app.get("/health")
def liveness():
    """Unauthenticated liveness probe for Railway (must not depend on DB)."""
    return JSONResponse({"status": "ok", "app": settings.app_name})


@app.get("/api/health")
def api_health():
    payload = {
        "status": "ok" if _db_ready else "starting",
        "app": settings.app_name,
        "environment": settings.environment,
        "database_ready": _db_ready,
    }
    if _db_error and not _db_ready:
        payload["database_error"] = _db_error
    return JSONResponse(payload)


if STATIC_DIR.exists() and (STATIC_DIR / "index.html").exists():
    assets_dir = STATIC_DIR / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    def spa_fallback(full_path: str = ""):  # noqa: ARG001
        if full_path.startswith("api/"):
            return JSONResponse({"detail": "Not Found"}, status_code=404)
        index = STATIC_DIR / "index.html"
        candidate = STATIC_DIR / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(index)
