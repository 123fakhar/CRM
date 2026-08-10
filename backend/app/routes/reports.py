from datetime import datetime

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.auth.security import AdminUser, AnyAuthUser
from app.core.database import get_db
from app.schemas import DashboardOut
from app.services.export import export_csv, export_xlsx
from app.services.stats import build_dashboard

router = APIRouter(prefix="/api", tags=["reports"])


@router.get("/dashboard", response_model=DashboardOut)
def dashboard(
    current_user: AnyAuthUser,
    db: Session = Depends(get_db),
    month: int | None = Query(None, ge=1, le=12),
    year: int | None = Query(None, ge=2000, le=2100),
):
    return build_dashboard(db, current_user, month=month, year=year)


@router.get("/reports/export")
def export_report(
    admin: AdminUser,
    db: Session = Depends(get_db),
    format: str = Query("csv", pattern="^(csv|xlsx)$"),
    search: str | None = None,
    agent_id: int | None = None,
    closer_id: int | None = None,
    campaign_id: int | None = None,
    initial_status: str | None = None,
    buyer_response: str | None = None,
    final_status: str | None = None,
    state: str | None = None,
    date_preset: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    month: int | None = Query(None, ge=1, le=12),
    year: int | None = Query(None, ge=2000, le=2100),
):
    filters = dict(
        search=search,
        agent_id=agent_id,
        closer_id=closer_id,
        campaign_id=campaign_id,
        initial_status=initial_status,
        buyer_response=buyer_response,
        final_status=final_status,
        state=state,
        date_preset=date_preset,
        date_from=date_from,
        date_to=date_to,
        month=month,
        year=year,
    )
    if format == "xlsx":
        content = export_xlsx(db, admin, **filters)
        return Response(
            content=content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=seagulls_leads_export.xlsx"},
        )
    content = export_csv(db, admin, **filters)
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=seagulls_leads_export.csv"},
    )
