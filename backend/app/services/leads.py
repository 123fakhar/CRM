import re
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.sql import func

from app.core.config import get_settings
from app.core.constants import (
    US_STATES,
    BuyerResponse,
    FinalStatus,
    InitialStatus,
    RejectionReason,
    UserRole,
)
from app.models import Agent, Campaign, Closer, Lead, User
from app.schemas import LeadAdminUpdate, LeadCreate, LeadOut, PerformanceRow, StatsSummary
from app.services.audit import write_audit

settings = get_settings()
ZIP_RE = re.compile(r"^\d{5}(-\d{4})?$")


def validate_zip(zip_code: str) -> str:
    z = zip_code.strip()
    if not ZIP_RE.match(z):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="ZipCode must be 5 digits or ZIP+4 (e.g. 12345 or 12345-6789)",
        )
    return z


def validate_state(state: str) -> str:
    s = state.strip().upper()
    if s not in US_STATES:
        raise HTTPException(status_code=422, detail=f"Invalid state: {state}")
    return s


def next_lead_number(db: Session) -> int:
    current = db.query(func.max(Lead.lead_number)).scalar()
    if current is None:
        return settings.lead_number_start
    return int(current) + 1


def lead_to_out(lead: Lead) -> LeadOut:
    return LeadOut(
        id=lead.id,
        lead_number=lead.lead_number,
        customer_number=lead.customer_number,
        first_name=lead.first_name,
        last_name=lead.last_name,
        state=lead.state,
        zip_code=lead.zip_code,
        agent_id=lead.agent_id,
        closer_id=lead.closer_id,
        campaign_id=lead.campaign_id,
        agent_name=lead.agent.name if lead.agent else "",
        closer_name=lead.closer.name if lead.closer else "",
        campaign_name=lead.campaign.name if lead.campaign else "",
        did=lead.did,
        d1=lead.d1,
        other=lead.other,
        comments=lead.comments,
        initial_status=lead.initial_status,
        buyer_response=lead.buyer_response,
        final_status=lead.final_status,
        rejection_reason=lead.rejection_reason,
        admin_notes=lead.admin_notes,
        submitted_at=lead.submitted_at,
        buyer_response_at=lead.buyer_response_at,
        finalized_at=lead.finalized_at,
        updated_at=lead.updated_at,
        created_by=lead.created_by,
        updated_by=lead.updated_by,
    )


def get_closer_for_user(db: Session, user: User) -> Closer:
    closer = db.query(Closer).filter(Closer.user_id == user.id, Closer.active.is_(True)).first()
    if not closer:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No active Closer profile is associated with this account",
        )
    return closer


def get_agent_for_user(db: Session, user: User) -> Agent | None:
    return db.query(Agent).filter(Agent.user_id == user.id).first()


def create_lead(db: Session, payload: LeadCreate, user: User) -> Lead:
    if user.role not in (UserRole.CLOSER.value, UserRole.ADMIN.value):
        raise HTTPException(status_code=403, detail="Only Closers (or Admin) can submit sales forms")

    state = validate_state(payload.state)
    zip_code = validate_zip(payload.zip_code)

    agent = db.query(Agent).filter(Agent.id == payload.agent_id, Agent.active.is_(True)).first()
    if not agent:
        raise HTTPException(status_code=422, detail="Invalid or inactive Agent")

    campaign = (
        db.query(Campaign)
        .filter(Campaign.id == payload.campaign_id, Campaign.active.is_(True))
        .first()
    )
    if not campaign:
        raise HTTPException(status_code=422, detail="Invalid or inactive Campaign")

    if user.role == UserRole.CLOSER.value:
        closer = get_closer_for_user(db, user)
    else:
        closer = db.query(Closer).filter(Closer.user_id == user.id, Closer.active.is_(True)).first()
        if closer is None:
            raise HTTPException(
                status_code=403,
                detail="Sales form submission requires a Closer profile. Use a Closer account.",
            )

    recent_cutoff = datetime.now(timezone.utc) - timedelta(minutes=5)
    dup = (
        db.query(Lead)
        .filter(
            Lead.customer_number == payload.customer_number.strip(),
            Lead.agent_id == agent.id,
            Lead.closer_id == closer.id,
            Lead.submitted_at >= recent_cutoff,
        )
        .first()
    )
    if dup:
        raise HTTPException(
            status_code=409,
            detail="A similar lead was submitted recently. Possible duplicate submission.",
        )

    lead = Lead(
        lead_number=next_lead_number(db),
        customer_number=payload.customer_number.strip(),
        first_name=payload.first_name.strip(),
        last_name=payload.last_name.strip(),
        state=state,
        zip_code=zip_code,
        agent_id=agent.id,
        closer_id=closer.id,
        campaign_id=campaign.id,
        did=payload.did.strip(),
        d1=payload.d1.strip() if payload.d1 else None,
        other=payload.other.strip() if payload.other else None,
        comments=payload.comments.strip() if payload.comments else None,
        initial_status=InitialStatus.PENDING.value,
        buyer_response=BuyerResponse.PENDING_NOT_RECEIVED.value,
        final_status=FinalStatus.PENDING.value,
        submitted_at=datetime.now(timezone.utc),
        created_by=user.id,
        updated_by=user.id,
    )
    db.add(lead)
    db.flush()
    write_audit(
        db,
        user=user,
        action="Created Lead",
        entity="Lead",
        entity_id=lead.lead_number,
        new_value=f"Lead #{lead.lead_number} created — Final Status: Pending",
    )
    db.commit()
    db.refresh(lead)
    return (
        db.query(Lead)
        .options(joinedload(Lead.agent), joinedload(Lead.closer), joinedload(Lead.campaign))
        .filter(Lead.id == lead.id)
        .one()
    )


def update_lead_admin(db: Session, lead_id: int, payload: LeadAdminUpdate, user: User) -> Lead:
    if user.role != UserRole.ADMIN.value:
        raise HTTPException(status_code=403, detail="Only Admin can edit leads")

    lead = (
        db.query(Lead)
        .options(joinedload(Lead.agent), joinedload(Lead.closer), joinedload(Lead.campaign))
        .filter(Lead.id == lead_id)
        .first()
    )
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    data = payload.model_dump(exclude_unset=True)
    now = datetime.now(timezone.utc)

    # Normalize blank rejection reasons so validation is consistent.
    if "rejection_reason" in data and isinstance(data["rejection_reason"], str):
        data["rejection_reason"] = data["rejection_reason"].strip() or None

    if "state" in data and data["state"] is not None:
        data["state"] = validate_state(data["state"])
    if "zip_code" in data and data["zip_code"] is not None:
        data["zip_code"] = validate_zip(data["zip_code"])

    if "agent_id" in data and data["agent_id"] is not None:
        if not db.query(Agent).filter(Agent.id == data["agent_id"]).first():
            raise HTTPException(status_code=422, detail="Invalid Agent")
    if "closer_id" in data and data["closer_id"] is not None:
        if not db.query(Closer).filter(Closer.id == data["closer_id"]).first():
            raise HTTPException(status_code=422, detail="Invalid Closer")
    if "campaign_id" in data and data["campaign_id"] is not None:
        if not db.query(Campaign).filter(Campaign.id == data["campaign_id"]).first():
            raise HTTPException(status_code=422, detail="Invalid Campaign")

    # Resolve the effective final status / rejection reason for this update
    # BEFORE writing audit rows or mutating the ORM object.
    effective_final_status = data.get("final_status", lead.final_status)
    if "final_status" in data and data["final_status"] is not None:
        valid_fs = {f.value for f in FinalStatus}
        if data["final_status"] not in valid_fs:
            raise HTTPException(status_code=422, detail="Invalid Final Status")

    if effective_final_status == FinalStatus.REJECTED.value:
        if "rejection_reason" in data:
            reason = data["rejection_reason"]
        else:
            reason = lead.rejection_reason
        if not reason:
            raise HTTPException(
                status_code=422,
                detail="Rejected leads require a rejection reason.",
            )
        valid_rr = {r.value for r in RejectionReason}
        if reason not in valid_rr:
            raise HTTPException(status_code=422, detail="Invalid rejection reason")
        data["rejection_reason"] = reason
    elif effective_final_status in (FinalStatus.ACCEPTED.value, FinalStatus.PENDING.value):
        # Accepted/Pending leads must not keep a stale rejection reason.
        data["rejection_reason"] = None

    if "buyer_response" in data and data["buyer_response"] is not None:
        valid_br = {b.value for b in BuyerResponse}
        if data["buyer_response"] not in valid_br:
            raise HTTPException(status_code=422, detail="Invalid Buyer Response")
        if data["buyer_response"] != lead.buyer_response:
            write_audit(
                db,
                user=user,
                action="Buyer Response Changed",
                entity="Lead",
                entity_id=lead.lead_number,
                old_value=lead.buyer_response,
                new_value=data["buyer_response"],
            )
            data["buyer_response_at"] = now

    if "final_status" in data and data["final_status"] is not None:
        if data["final_status"] != lead.final_status:
            write_audit(
                db,
                user=user,
                action="Final Status Changed",
                entity="Lead",
                entity_id=lead.lead_number,
                old_value=lead.final_status,
                new_value=data["final_status"],
            )
            if data["final_status"] in (FinalStatus.ACCEPTED.value, FinalStatus.REJECTED.value):
                data["finalized_at"] = now

    if "rejection_reason" in data and data["rejection_reason"] != lead.rejection_reason:
        write_audit(
            db,
            user=user,
            action="Rejection Reason Changed",
            entity="Lead",
            entity_id=lead.lead_number,
            old_value=lead.rejection_reason,
            new_value=data["rejection_reason"],
        )

    if "admin_notes" in data and data["admin_notes"] != lead.admin_notes:
        write_audit(
            db,
            user=user,
            action="Admin Notes Updated",
            entity="Lead",
            entity_id=lead.lead_number,
            old_value=lead.admin_notes,
            new_value=data["admin_notes"],
        )

    for field in [
        "customer_number",
        "first_name",
        "last_name",
        "state",
        "zip_code",
        "agent_id",
        "closer_id",
        "campaign_id",
        "did",
        "d1",
        "other",
        "comments",
    ]:
        if field in data and getattr(lead, field) != data[field]:
            write_audit(
                db,
                user=user,
                action=f"{field.replace('_', ' ').title()} Changed",
                entity="Lead",
                entity_id=lead.lead_number,
                old_value=str(getattr(lead, field)),
                new_value=str(data[field]),
            )

    for key, value in data.items():
        setattr(lead, key, value)

    lead.updated_by = user.id
    lead.updated_at = now
    db.commit()
    db.refresh(lead)
    return (
        db.query(Lead)
        .options(joinedload(Lead.agent), joinedload(Lead.closer), joinedload(Lead.campaign))
        .filter(Lead.id == lead.id)
        .one()
    )


def delete_lead(db: Session, lead_id: int, user: User) -> None:
    if user.role != UserRole.ADMIN.value:
        raise HTTPException(status_code=403, detail="Only Admin can delete leads")
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    lead_number = lead.lead_number
    write_audit(
        db,
        user=user,
        action="Deleted Lead",
        entity="Lead",
        entity_id=lead_number,
        old_value=f"Lead #{lead_number}",
    )
    db.delete(lead)
    db.commit()


def parse_date_range(
    date_preset: str | None,
    date_from: datetime | None,
    date_to: datetime | None,
) -> tuple[datetime | None, datetime | None]:
    now = datetime.now(timezone.utc)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)

    if date_preset == "today":
        return today, today + timedelta(days=1)
    if date_preset == "yesterday":
        return today - timedelta(days=1), today
    if date_preset == "this_week":
        start = today - timedelta(days=today.weekday())
        return start, today + timedelta(days=1)
    if date_preset == "this_month":
        start = today.replace(day=1)
        return start, today + timedelta(days=1)
    if date_preset == "last_month":
        first_this = today.replace(day=1)
        last_month_start = (first_this - timedelta(days=1)).replace(day=1)
        return last_month_start, first_this
    if date_preset == "custom" or date_from or date_to:
        end = date_to
        if end and end.hour == 0 and end.minute == 0 and end.second == 0:
            end = end + timedelta(days=1)
        return date_from, end
    return date_from, date_to


def build_lead_query(
    db: Session,
    user: User,
    *,
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
    month: int | None = None,
    year: int | None = None,
):
    q = (
        db.query(Lead)
        .options(joinedload(Lead.agent), joinedload(Lead.closer), joinedload(Lead.campaign))
        .join(Agent, Lead.agent_id == Agent.id)
        .join(Closer, Lead.closer_id == Closer.id)
        .join(Campaign, Lead.campaign_id == Campaign.id)
    )

    if user.role == UserRole.AGENT.value:
        agent = get_agent_for_user(db, user)
        if not agent:
            return q.filter(Lead.id == -1)
        q = q.filter(Lead.agent_id == agent.id)
    elif user.role == UserRole.CLOSER.value:
        closer = db.query(Closer).filter(Closer.user_id == user.id).first()
        if not closer:
            return q.filter(Lead.id == -1)
        q = q.filter(Lead.closer_id == closer.id)

    if search:
        term = f"%{search.strip()}%"
        or_filters = [
            Lead.customer_number.ilike(term),
            Lead.first_name.ilike(term),
            Lead.last_name.ilike(term),
            Agent.name.ilike(term),
            Closer.name.ilike(term),
        ]
        digits = search.strip().lstrip("#")
        if digits.isdigit():
            or_filters.append(Lead.lead_number == int(digits))
        q = q.filter(or_(*or_filters))

    if agent_id:
        q = q.filter(Lead.agent_id == agent_id)
    if closer_id:
        q = q.filter(Lead.closer_id == closer_id)
    if campaign_id:
        q = q.filter(Lead.campaign_id == campaign_id)
    if initial_status:
        q = q.filter(Lead.initial_status == initial_status)
    if buyer_response:
        q = q.filter(Lead.buyer_response == buyer_response)
    if final_status:
        q = q.filter(Lead.final_status == final_status)
    if state:
        q = q.filter(Lead.state == state.upper())

    start, end = parse_date_range(date_preset, date_from, date_to)
    if month and year:
        start = datetime(year, month, 1, tzinfo=timezone.utc)
        end = (
            datetime(year + 1, 1, 1, tzinfo=timezone.utc)
            if month == 12
            else datetime(year, month + 1, 1, tzinfo=timezone.utc)
        )
    if start:
        q = q.filter(Lead.submitted_at >= start)
    if end:
        q = q.filter(Lead.submitted_at < end)

    return q


def calc_rates(accepted: int, rejected: int, total: int) -> tuple[float, float]:
    if total == 0:
        return 0.0, 0.0
    return round(accepted / total * 100, 2), round(rejected / total * 100, 2)


def summarize_leads(leads: list[Lead]) -> StatsSummary:
    total = len(leads)
    accepted = sum(1 for lead in leads if lead.final_status == FinalStatus.ACCEPTED.value)
    rejected = sum(1 for lead in leads if lead.final_status == FinalStatus.REJECTED.value)
    pending = sum(1 for lead in leads if lead.final_status == FinalStatus.PENDING.value)
    acc, rej = calc_rates(accepted, rejected, total)
    return StatsSummary(
        total_leads=total,
        accepted=accepted,
        rejected=rejected,
        pending=pending,
        acceptance_rate=acc,
        rejection_rate=rej,
    )


def group_performance(leads: list[Lead], key: str, name_map: dict[int, str]) -> list[PerformanceRow]:
    buckets: dict[int, list[Lead]] = {}
    for lead in leads:
        eid = getattr(lead, key)
        buckets.setdefault(eid, []).append(lead)

    rows: list[PerformanceRow] = []
    for eid, subset in buckets.items():
        summary = summarize_leads(subset)
        rows.append(
            PerformanceRow(
                id=eid,
                name=name_map.get(eid, f"#{eid}"),
                total_leads=summary.total_leads,
                accepted=summary.accepted,
                rejected=summary.rejected,
                pending=summary.pending,
                acceptance_rate=summary.acceptance_rate,
                rejection_rate=summary.rejection_rate,
            )
        )
    rows.sort(key=lambda r: (-r.accepted, -r.total_leads, r.name.lower()))
    return rows
