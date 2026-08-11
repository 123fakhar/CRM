from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

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

settings = get_settings()
STATIC_DIR = Path(settings.static_dir)


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_if_empty(db)
    finally:
        db.close()
    yield


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)

# Same-origin SPA (FastAPI serves UI + /api) does not need wildcard CORS.
# If a separate frontend origin is used, set CORS_ORIGINS to that exact origin.
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


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.environment,
    }


if STATIC_DIR.exists() and (STATIC_DIR / "index.html").exists():
    assets_dir = STATIC_DIR / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    def spa_fallback(full_path: str = ""):  # noqa: ARG001
        index = STATIC_DIR / "index.html"
        candidate = STATIC_DIR / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(index)
