"""
Database bootstrap helpers.

- Development/test: optional demo seed (never treated as real company data)
- Production: only creates an Admin when BOOTSTRAP_ADMIN_* env vars are set
"""

from sqlalchemy.orm import Session

from app.auth.security import hash_password
from app.core.config import get_settings
from app.core.constants import UserRole
from app.models import Agent, Campaign, Closer, User
from app.services.audit import write_audit


def seed_if_empty(db: Session) -> None:
    if db.query(User).count() > 0:
        return

    settings = get_settings()

    if settings.environment.lower() == "production":
        _bootstrap_production_admin(db)
        return

    _seed_demo_data(db)


def _bootstrap_production_admin(db: Session) -> None:
    settings = get_settings()
    email = (settings.bootstrap_admin_email or "").strip().lower()
    password = settings.bootstrap_admin_password or ""
    name = (settings.bootstrap_admin_name or "System Admin").strip()

    if not email or not password:
        # Production DB stays empty until bootstrap credentials are provided.
        return

    if len(password) < 8:
        raise ValueError("BOOTSTRAP_ADMIN_PASSWORD must be at least 8 characters")

    admin = User(
        name=name,
        email=email,
        password_hash=hash_password(password),
        role=UserRole.ADMIN.value,
        active=True,
    )
    db.add(admin)
    db.flush()
    write_audit(
        db,
        user=admin,
        action="Bootstrapped Admin",
        entity="User",
        entity_id=admin.id,
        new_value=f"Production admin created for {email}",
    )
    db.commit()


def _seed_demo_data(db: Session) -> None:
    admin = User(
        name="System Admin",
        email="admin@seagullsdemo.com",
        password_hash=hash_password("Admin123!"),
        role=UserRole.ADMIN.value,
        active=True,
    )
    db.add(admin)
    db.flush()

    agent_user = User(
        name="Demo Agent",
        email="agent@seagullsdemo.com",
        password_hash=hash_password("Agent123!"),
        role=UserRole.AGENT.value,
        active=True,
    )
    closer_user = User(
        name="Demo Closer",
        email="closer@seagullsdemo.com",
        password_hash=hash_password("Closer123!"),
        role=UserRole.CLOSER.value,
        active=True,
    )
    db.add_all([agent_user, closer_user])
    db.flush()

    agent = Agent(name="Demo Agent (TEST)", user_id=agent_user.id, active=True)
    agent2 = Agent(name="Demo Agent 2 (TEST)", active=True)
    closer = Closer(name="Demo Closer (TEST)", user_id=closer_user.id, active=True)
    closer2 = Closer(name="Demo Closer 2 (TEST)", active=True)
    camp1 = Campaign(name="Demo Campaign A (TEST)", active=True)
    camp2 = Campaign(name="Demo Campaign B (TEST)", active=True)
    db.add_all([agent, agent2, closer, closer2, camp1, camp2])
    db.flush()

    write_audit(
        db,
        user=admin,
        action="Seeded Database",
        entity="System",
        entity_id="seed",
        new_value="Created TEST seed users, agents, closers, and campaigns",
    )
    db.commit()
