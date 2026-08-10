from datetime import datetime
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.auth.security import AdminUser, AnyAuthUser, CloserUser
from app.core.database import get_db
from app.models import Lead
from app.schemas import LeadAdminUpdate, LeadCreate, LeadOut, MessageOut, PaginatedLeads
from app.services.leads import (
    build_lead_query,
    create_lead,
    delete_lead,
    lead_to_out,
    update_lead_admin,
)

router = APIRouter(prefix="/api/leads", tags=["leads"])


@router.post("", response_model=LeadOut, status_code=201)
def submit_lead(payload: LeadCreate, current_user: CloserUser, db: Session = Depends(get_db)):
    lead = create_lead(db, payload, current_user)
    return lead_to_out(lead)


@router.get("", response_model=PaginatedLeads)
def list_leads(
    current_user: AnyAuthUser,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
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
    q = build_lead_query(
        db,
        current_user,
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
    total = q.order_by(None).count()
    items = (
        q.order_by(Lead.submitted_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return PaginatedLeads(
        items=[lead_to_out(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=ceil(total / page_size) if total else 0,
    )


@router.get("/{lead_id}", response_model=LeadOut)
def get_lead(lead_id: int, current_user: AnyAuthUser, db: Session = Depends(get_db)):
    lead = (
        db.query(Lead)
        .options(joinedload(Lead.agent), joinedload(Lead.closer), joinedload(Lead.campaign))
        .filter(Lead.id == lead_id)
        .first()
    )
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # enforce scoped access
    if current_user.role == "agent":
        if not current_user.agent_profile or lead.agent_id != current_user.agent_profile.id:
            raise HTTPException(status_code=403, detail="Access denied")
    if current_user.role == "closer":
        if not current_user.closer_profile or lead.closer_id != current_user.closer_profile.id:
            raise HTTPException(status_code=403, detail="Access denied")

    return lead_to_out(lead)


@router.put("/{lead_id}", response_model=LeadOut)
def put_lead(
    lead_id: int,
    payload: LeadAdminUpdate,
    admin: AdminUser,
    db: Session = Depends(get_db),
):
    lead = update_lead_admin(db, lead_id, payload, admin)
    return lead_to_out(lead)


@router.patch("/{lead_id}", response_model=LeadOut)
def patch_lead(
    lead_id: int,
    payload: LeadAdminUpdate,
    admin: AdminUser,
    db: Session = Depends(get_db),
):
    lead = update_lead_admin(db, lead_id, payload, admin)
    return lead_to_out(lead)


@router.delete("/{lead_id}", response_model=MessageOut)
def remove_lead(lead_id: int, admin: AdminUser, db: Session = Depends(get_db)):
    delete_lead(db, lead_id, admin)
    return MessageOut(message="Lead deleted successfully")
