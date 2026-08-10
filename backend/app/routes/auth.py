from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.auth.security import (
    authenticate_user,
    create_access_token,
    get_current_user,
)
from app.core.config import get_settings
from app.core.database import get_db
from app.models import User
from app.schemas import LoginRequest, MeOut, Token
from app.services.audit import write_audit

router = APIRouter(prefix="/api/auth", tags=["auth"])
settings = get_settings()


def user_to_me(user: User) -> MeOut:
    return MeOut(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        active=user.active,
        created_at=user.created_at,
        updated_at=user.updated_at,
        agent_id=user.agent_profile.id if user.agent_profile else None,
        closer_id=user.closer_profile.id if user.closer_profile else None,
        agent_name=user.agent_profile.name if user.agent_profile else None,
        closer_name=user.closer_profile.name if user.closer_profile else None,
    )


@router.post("/login", response_model=Token)
def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    token = create_access_token(
        {"sub": str(user.id), "role": user.role},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )
    write_audit(db, user=user, action="Login", entity="User", entity_id=user.id)
    db.commit()
    return Token(access_token=token)


@router.post("/login/json", response_model=Token)
def login_json(payload: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    token = create_access_token(
        {"sub": str(user.id), "role": user.role},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )
    write_audit(db, user=user, action="Login", entity="User", entity_id=user.id)
    db.commit()
    return Token(access_token=token)


@router.get("/me", response_model=MeOut)
def me(current_user: User = Depends(get_current_user)):
    return user_to_me(current_user)


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    write_audit(db, user=current_user, action="Logout", entity="User", entity_id=current_user.id)
    db.commit()
    return {"message": "Logged out successfully"}
