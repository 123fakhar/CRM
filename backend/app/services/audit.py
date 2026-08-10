from sqlalchemy.orm import Session

from app.models import AuditLog, User


def write_audit(
    db: Session,
    *,
    user: User | None,
    action: str,
    entity: str,
    entity_id: str | int | None = None,
    old_value: str | None = None,
    new_value: str | None = None,
    user_name: str | None = None,
    role: str | None = None,
) -> AuditLog:
    entry = AuditLog(
        user_id=user.id if user else None,
        user_name=user_name or (user.name if user else "System"),
        role=role or (user.role if user else "system"),
        action=action,
        entity=entity,
        entity_id=str(entity_id) if entity_id is not None else None,
        old_value=old_value,
        new_value=new_value,
    )
    db.add(entry)
    return entry
