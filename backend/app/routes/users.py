from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.security import AdminUser, hash_password
from app.core.constants import UserRole
from app.core.database import get_db
from app.models import Agent, Closer, User
from app.schemas import MessageOut, PasswordReset, UserCreate, UserOut, UserUpdate
from app.services.audit import write_audit
from app.routes.auth import user_to_me

router = APIRouter(prefix="/api/users", tags=["users"])


def to_user_out(user: User) -> UserOut:
    return user_to_me(user)


@router.get("", response_model=list[UserOut])
def list_users(admin: AdminUser, db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.created_at.desc()).all()
    return [to_user_out(u) for u in users]


@router.post("", response_model=UserOut, status_code=201)
def create_user(payload: UserCreate, admin: AdminUser, db: Session = Depends(get_db)):
    role = payload.role.lower()
    if role not in {r.value for r in UserRole}:
        raise HTTPException(status_code=422, detail="Invalid role")

    if db.query(User).filter(User.email == payload.email.lower()).first():
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        name=payload.name.strip(),
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        role=role,
        active=payload.active,
    )
    db.add(user)
    db.flush()

    if role == UserRole.AGENT.value:
        name = (payload.agent_name or payload.name).strip()
        existing = db.query(Agent).filter(Agent.name == name).first()
        if existing and existing.user_id and existing.user_id != user.id:
            raise HTTPException(status_code=409, detail="Agent name already linked to another user")
        if existing:
            existing.user_id = user.id
            existing.active = True
        else:
            db.add(Agent(name=name, user_id=user.id, active=True))

    if role == UserRole.CLOSER.value:
        name = (payload.closer_name or payload.name).strip()
        existing = db.query(Closer).filter(Closer.name == name).first()
        if existing and existing.user_id and existing.user_id != user.id:
            raise HTTPException(status_code=409, detail="Closer name already linked to another user")
        if existing:
            existing.user_id = user.id
            existing.active = True
        else:
            db.add(Closer(name=name, user_id=user.id, active=True))

    write_audit(
        db,
        user=admin,
        action="Created User",
        entity="User",
        entity_id=user.id,
        new_value=f"{user.name} ({user.role})",
    )
    db.commit()
    db.refresh(user)
    return to_user_out(user)


@router.patch("/{user_id}", response_model=UserOut)
def update_user(user_id: int, payload: UserUpdate, admin: AdminUser, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    data = payload.model_dump(exclude_unset=True)
    if "email" in data and data["email"]:
        data["email"] = data["email"].lower()
        clash = db.query(User).filter(User.email == data["email"], User.id != user_id).first()
        if clash:
            raise HTTPException(status_code=409, detail="Email already registered")
    if "role" in data and data["role"]:
        data["role"] = data["role"].lower()
        if data["role"] not in {r.value for r in UserRole}:
            raise HTTPException(status_code=422, detail="Invalid role")

    for key in ("name", "email", "role", "active"):
        if key in data and getattr(user, key) != data[key]:
            write_audit(
                db,
                user=admin,
                action=f"User {key.replace('_', ' ').title()} Changed",
                entity="User",
                entity_id=user.id,
                old_value=str(getattr(user, key)),
                new_value=str(data[key]),
            )
            setattr(user, key, data[key])

    if user.role == UserRole.AGENT.value and payload.agent_name:
        if user.agent_profile:
            user.agent_profile.name = payload.agent_name.strip()
        else:
            db.add(Agent(name=payload.agent_name.strip(), user_id=user.id, active=True))

    if user.role == UserRole.CLOSER.value and payload.closer_name:
        if user.closer_profile:
            user.closer_profile.name = payload.closer_name.strip()
        else:
            db.add(Closer(name=payload.closer_name.strip(), user_id=user.id, active=True))

    db.commit()
    db.refresh(user)
    return to_user_out(user)


@router.post("/{user_id}/reset-password", response_model=MessageOut)
def reset_password(
    user_id: int, payload: PasswordReset, admin: AdminUser, db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.password_hash = hash_password(payload.new_password)
    write_audit(
        db,
        user=admin,
        action="Password Reset",
        entity="User",
        entity_id=user.id,
        new_value="Password reset by admin",
    )
    db.commit()
    return MessageOut(message="Password reset successfully")


@router.delete("/{user_id}", response_model=MessageOut)
def delete_user(user_id: int, admin: AdminUser, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    write_audit(
        db,
        user=admin,
        action="Deleted User",
        entity="User",
        entity_id=user.id,
        old_value=f"{user.name} ({user.email})",
    )
    if user.agent_profile:
        user.agent_profile.user_id = None
    if user.closer_profile:
        user.closer_profile.user_id = None
    db.delete(user)
    db.commit()
    return MessageOut(message="User deleted")
