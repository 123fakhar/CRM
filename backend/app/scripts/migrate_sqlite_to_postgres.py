"""
Migrate data from a local SQLite DB into PostgreSQL.

Usage (from backend/ with venv active):
  python -m app.scripts.migrate_sqlite_to_postgres

Requires DATABASE_URL to point at PostgreSQL and SQLITE_SOURCE_URL
(or defaults to sqlite:///./seagulls_crm.db).
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import Base
from app.models import Agent, AuditLog, Campaign, Closer, Lead, User


TABLE_ORDER = [User, Agent, Closer, Campaign, Lead, AuditLog]


def _copy_table(src: Session, dest: Session, model) -> int:
    rows = src.scalars(select(model)).all()
    if not rows:
        return 0

    payload = []
    for row in rows:
        data = {c.name: getattr(row, c.name) for c in model.__table__.columns}
        payload.append(model(**data))

    dest.add_all(payload)
    dest.flush()
    return len(payload)


def migrate(sqlite_url: str, postgres_url: str) -> None:
    if not postgres_url.startswith("postgresql"):
        raise SystemExit("DATABASE_URL must be a PostgreSQL URL for migration target.")

    src_engine = create_engine(
        sqlite_url,
        connect_args={"check_same_thread": False} if sqlite_url.startswith("sqlite") else {},
    )
    dest_engine = create_engine(postgres_url)

    Base.metadata.create_all(bind=dest_engine)

    SrcSession = sessionmaker(bind=src_engine)
    DestSession = sessionmaker(bind=dest_engine)

    with SrcSession() as src, DestSession() as dest:
        # Abort if destination already has users (avoid duplicate seed+migrate)
        existing = dest.scalar(select(User.id).limit(1))
        if existing is not None:
            raise SystemExit(
                "PostgreSQL already has users. Empty the DB first or skip migration."
            )

        counts: dict[str, int] = {}
        for model in TABLE_ORDER:
            counts[model.__tablename__] = _copy_table(src, dest, model)

        # Reset sequences so new IDs continue after migrated max IDs
        for model in TABLE_ORDER:
            table = model.__tablename__
            pk = list(model.__table__.primary_key.columns)[0].name
            dest.execute(
                text(
                    f"""
                    SELECT setval(
                      pg_get_serial_sequence(:table_name, :pk),
                      COALESCE((SELECT MAX({pk}) FROM {table}), 1),
                      true
                    )
                    """
                ),
                {"table_name": table, "pk": pk},
            )

        dest.commit()
        print(f"Migration complete at {datetime.now(timezone.utc).isoformat()}")
        for name, count in counts.items():
            print(f"  {name}: {count} rows")


def main() -> None:
    sqlite_url = os.getenv("SQLITE_SOURCE_URL", "sqlite:///./seagulls_crm.db")
    postgres_url = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://seagulls:seagulls_crm_dev@localhost:5432/seagulls_crm",
    )
    migrate(sqlite_url, postgres_url)


if __name__ == "__main__":
    main()
