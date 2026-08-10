from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.security import AdminUser, AnyAuthUser
from app.core.database import get_db
from app.models import Closer
from app.schemas import CloserCreate, CloserOut, CloserUpdate, MessageOut
from app.services.audit import write_audit

router = APIRouter(prefix="/api/closers", tags=["closers"])


@router.get("", response_model=list[CloserOut])
def list_closers(
    current_user: AnyAuthUser,
    db: Session = Depends(get_db),
    active_only: bool = False,
):
    q = db.query(Closer)
    if active_only or current_user.role != "admin":
        q = q.filter(Closer.active.is_(True))
    return q.order_by(Closer.name.asc()).all()


@router.post("", response_model=CloserOut, status_code=201)
def create_closer(payload: CloserCreate, admin: AdminUser, db: Session = Depends(get_db)):
    if db.query(Closer).filter(Closer.name == payload.name.strip()).first():
        raise HTTPException(status_code=409, detail="Closer name already exists")
    closer = Closer(name=payload.name.strip(), user_id=payload.user_id, active=payload.active)
    db.add(closer)
    db.flush()
    write_audit(
        db,
        user=admin,
        action="Created Closer",
        entity="Closer",
        entity_id=closer.id,
        new_value=closer.name,
    )
    db.commit()
    db.refresh(closer)
    return closer


@router.patch("/{closer_id}", response_model=CloserOut)
def update_closer(
    closer_id: int, payload: CloserUpdate, admin: AdminUser, db: Session = Depends(get_db)
):
    closer = db.query(Closer).filter(Closer.id == closer_id).first()
    if not closer:
        raise HTTPException(status_code=404, detail="Closer not found")
    data = payload.model_dump(exclude_unset=True)
    if "name" in data and data["name"]:
        clash = (
            db.query(Closer).filter(Closer.name == data["name"].strip(), Closer.id != closer_id).first()
        )
        if clash:
            raise HTTPException(status_code=409, detail="Closer name already exists")
        data["name"] = data["name"].strip()
    for key, value in data.items():
        old = getattr(closer, key)
        if old != value:
            write_audit(
                db,
                user=admin,
                action=f"Closer {key.title()} Changed",
                entity="Closer",
                entity_id=closer.id,
                old_value=str(old),
                new_value=str(value),
            )
            setattr(closer, key, value)
    db.commit()
    db.refresh(closer)
    return closer


@router.delete("/{closer_id}", response_model=MessageOut)
def delete_closer(closer_id: int, admin: AdminUser, db: Session = Depends(get_db)):
    closer = db.query(Closer).filter(Closer.id == closer_id).first()
    if not closer:
        raise HTTPException(status_code=404, detail="Closer not found")
    if closer.leads:
        closer.active = False
        write_audit(
            db,
            user=admin,
            action="Deactivated Closer",
            entity="Closer",
            entity_id=closer.id,
            old_value="active",
            new_value="inactive",
        )
        db.commit()
        return MessageOut(message="Closer has leads and was deactivated instead of deleted")
    write_audit(
        db,
        user=admin,
        action="Deleted Closer",
        entity="Closer",
        entity_id=closer.id,
        old_value=closer.name,
    )
    db.delete(closer)
    db.commit()
    return MessageOut(message="Closer deleted")
