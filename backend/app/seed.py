"""
Seed/test data — clearly labeled for development only.
Does not invent real Seagulls business data as production truth.
"""

from sqlalchemy.orm import Session

from app.auth.security import hash_password
from app.core.constants import UserRole
from app.models import Agent, Campaign, Closer, User
from app.services.audit import write_audit


def seed_if_empty(db: Session) -> None:
    if db.query(User).count() > 0:
        return

    admin = User(
        name="System Admin",
        email="admin@seagullsdemo.com",
        password_hash=hash_password("Admin123!"),
        role=UserRole.ADMIN.value,
        active=True,
    )
    db.add(admin)
    db.flush()

    # Demo agents/closers/campaigns — TEST DATA ONLY
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
