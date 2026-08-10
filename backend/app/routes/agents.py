from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.security import AdminUser, AnyAuthUser
from app.core.database import get_db
from app.models import Agent
from app.schemas import AgentCreate, AgentOut, AgentUpdate, MessageOut
from app.services.audit import write_audit

router = APIRouter(prefix="/api/agents", tags=["agents"])


@router.get("", response_model=list[AgentOut])
def list_agents(
    current_user: AnyAuthUser,
    db: Session = Depends(get_db),
    active_only: bool = False,
):
    q = db.query(Agent)
    if active_only or current_user.role != "admin":
        q = q.filter(Agent.active.is_(True))
    return q.order_by(Agent.name.asc()).all()


@router.post("", response_model=AgentOut, status_code=201)
def create_agent(payload: AgentCreate, admin: AdminUser, db: Session = Depends(get_db)):
    if db.query(Agent).filter(Agent.name == payload.name.strip()).first():
        raise HTTPException(status_code=409, detail="Agent name already exists")
    agent = Agent(name=payload.name.strip(), user_id=payload.user_id, active=payload.active)
    db.add(agent)
    db.flush()
    write_audit(
        db, user=admin, action="Created Agent", entity="Agent", entity_id=agent.id, new_value=agent.name
    )
    db.commit()
    db.refresh(agent)
    return agent


@router.patch("/{agent_id}", response_model=AgentOut)
def update_agent(
    agent_id: int, payload: AgentUpdate, admin: AdminUser, db: Session = Depends(get_db)
):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    data = payload.model_dump(exclude_unset=True)
    if "name" in data and data["name"]:
        clash = db.query(Agent).filter(Agent.name == data["name"].strip(), Agent.id != agent_id).first()
        if clash:
            raise HTTPException(status_code=409, detail="Agent name already exists")
        data["name"] = data["name"].strip()
    for key, value in data.items():
        old = getattr(agent, key)
        if old != value:
            write_audit(
                db,
                user=admin,
                action=f"Agent {key.title()} Changed",
                entity="Agent",
                entity_id=agent.id,
                old_value=str(old),
                new_value=str(value),
            )
            setattr(agent, key, value)
    db.commit()
    db.refresh(agent)
    return agent


@router.delete("/{agent_id}", response_model=MessageOut)
def delete_agent(agent_id: int, admin: AdminUser, db: Session = Depends(get_db)):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    if agent.leads:
        agent.active = False
        write_audit(
            db,
            user=admin,
            action="Deactivated Agent",
            entity="Agent",
            entity_id=agent.id,
            old_value="active",
            new_value="inactive",
        )
        db.commit()
        return MessageOut(message="Agent has leads and was deactivated instead of deleted")
    write_audit(
        db, user=admin, action="Deleted Agent", entity="Agent", entity_id=agent.id, old_value=agent.name
    )
    db.delete(agent)
    db.commit()
    return MessageOut(message="Agent deleted")
