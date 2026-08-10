from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
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
    return {"status": "ok", "app": settings.app_name}
