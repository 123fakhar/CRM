from calendar import month_abbr
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import Agent, Campaign, Closer, Lead, User
from app.schemas import DashboardOut, MonthlyTrendPoint, PerformanceRow
from app.services.leads import (
    build_lead_query,
    get_agent_for_user,
    get_closer_for_user,
    group_performance,
    summarize_leads,
)
from app.core.constants import UserRole


def build_dashboard(
    db: Session,
    user: User,
    *,
    month: int | None = None,
    year: int | None = None,
) -> DashboardOut:
    q = build_lead_query(db, user, month=month, year=year)
    leads = q.all()
    summary = summarize_leads(leads)

    agents = {a.id: a.name for a in db.query(Agent).all()}
    closers = {c.id: c.name for c in db.query(Closer).all()}
    campaigns = {c.id: c.name for c in db.query(Campaign).all()}

    # Role-scoped performance views
    if user.role == UserRole.AGENT.value:
        agent = get_agent_for_user(db, user)
        agent_perf = group_performance(leads, "agent_id", agents)
        if agent:
            agent_perf = [r for r in agent_perf if r.id == agent.id]
        closer_perf = group_performance(leads, "closer_id", closers)
        campaign_perf = group_performance(leads, "campaign_id", campaigns)
    elif user.role == UserRole.CLOSER.value:
        closer = db.query(Closer).filter(Closer.user_id == user.id).first()
        agent_perf = group_performance(leads, "agent_id", agents)
        closer_perf = group_performance(leads, "closer_id", closers)
        if closer:
            closer_perf = [r for r in closer_perf if r.id == closer.id]
        campaign_perf = group_performance(leads, "campaign_id", campaigns)
    else:
        agent_perf = group_performance(leads, "agent_id", agents)
        closer_perf = group_performance(leads, "closer_id", closers)
        campaign_perf = group_performance(leads, "campaign_id", campaigns)

    # Ensure all active entities appear even with zero leads (admin only)
    if user.role == UserRole.ADMIN.value and not month:
        agent_perf = _ensure_entities(agent_perf, db.query(Agent).filter(Agent.active.is_(True)).all())
        closer_perf = _ensure_entities(
            closer_perf, db.query(Closer).filter(Closer.active.is_(True)).all()
        )
        campaign_perf = _ensure_entities(
            campaign_perf, db.query(Campaign).filter(Campaign.active.is_(True)).all()
        )

    trend = _monthly_trend(db, user)

    top_agent = max(agent_perf, key=lambda r: r.accepted, default=None) if agent_perf else None
    top_closer = max(closer_perf, key=lambda r: r.accepted, default=None) if closer_perf else None
    top_campaign = (
        max(campaign_perf, key=lambda r: r.accepted, default=None) if campaign_perf else None
    )

    return DashboardOut(
        summary=summary,
        agent_performance=agent_perf,
        closer_performance=closer_perf,
        campaign_performance=campaign_perf,
        monthly_trend=trend,
        top_agent=top_agent if top_agent and top_agent.accepted > 0 else top_agent,
        top_closer=top_closer if top_closer and top_closer.accepted > 0 else top_closer,
        top_campaign=top_campaign if top_campaign and top_campaign.accepted > 0 else top_campaign,
    )


def _ensure_entities(rows: list[PerformanceRow], entities) -> list[PerformanceRow]:
    existing = {r.id for r in rows}
    for entity in entities:
        if entity.id not in existing:
            rows.append(
                PerformanceRow(
                    id=entity.id,
                    name=entity.name,
                    total_leads=0,
                    accepted=0,
                    rejected=0,
                    pending=0,
                    acceptance_rate=0.0,
                    rejection_rate=0.0,
                )
            )
    rows.sort(key=lambda r: (-r.accepted, -r.total_leads, r.name.lower()))
    return rows


def _monthly_trend(db: Session, user: User, months: int = 6) -> list[MonthlyTrendPoint]:
    now = datetime.now(timezone.utc)
    points: list[MonthlyTrendPoint] = []
    for i in range(months - 1, -1, -1):
        y = now.year
        m = now.month - i
        while m <= 0:
            m += 12
            y -= 1
        q = build_lead_query(db, user, month=m, year=y)
        leads = q.all()
        summary = summarize_leads(leads)
        points.append(
            MonthlyTrendPoint(
                month=f"{month_abbr[m]} {y}",
                accepted=summary.accepted,
                rejected=summary.rejected,
                pending=summary.pending,
                total=summary.total_leads,
            )
        )
    return points
