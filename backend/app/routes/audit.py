from math import ceil

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.security import AdminUser
from app.core.database import get_db
from app.models import AuditLog
from app.schemas import AuditLogOut, PaginatedAudit

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("", response_model=PaginatedAudit)
def list_audit(
    admin: AdminUser,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    entity: str | None = None,
    action: str | None = None,
    search: str | None = None,
):
    q = db.query(AuditLog)
    if entity:
        q = q.filter(AuditLog.entity == entity)
    if action:
        q = q.filter(AuditLog.action.ilike(f"%{action}%"))
    if search:
        term = f"%{search}%"
        q = q.filter(
            (AuditLog.user_name.ilike(term))
            | (AuditLog.action.ilike(term))
            | (AuditLog.entity_id.ilike(term))
            | (AuditLog.old_value.ilike(term))
            | (AuditLog.new_value.ilike(term))
        )
    total = q.count()
    items = q.order_by(AuditLog.timestamp.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedAudit(
        items=[AuditLogOut.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=ceil(total / page_size) if total else 0,
    )
