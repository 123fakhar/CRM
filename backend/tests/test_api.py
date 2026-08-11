"""API tests for Seagulls CRM — auth, permissions, workflow, stats."""

import os

os.environ["DATABASE_URL"] = "sqlite:///./test_seagulls_crm.db"
os.environ["SECRET_KEY"] = "test-secret"

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Remove prior test DB
Path("test_seagulls_crm.db").unlink(missing_ok=True)

from app.main import app  # noqa: E402
from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.seed import seed_if_empty  # noqa: E402


@pytest.fixture(scope="module")
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    seed_if_empty(db)
    db.close()
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)


def login(client: TestClient, email: str, password: str) -> str:
    res = client.post("/api/auth/login/json", json={"email": email, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_health(client):
    live = client.get("/health")
    assert live.status_code == 200
    assert live.json()["status"] == "ok"

    api = client.get("/api/health")
    assert api.status_code == 200
    assert api.json()["app"]


def test_login_roles(client):
    for email, password in [
        ("admin@seagullsdemo.com", "Admin123!"),
        ("agent@seagullsdemo.com", "Agent123!"),
        ("closer@seagullsdemo.com", "Closer123!"),
    ]:
        token = login(client, email, password)
        me = client.get("/api/auth/me", headers=auth(token))
        assert me.status_code == 200
        assert me.json()["email"] == email


def test_agent_cannot_edit_or_delete(client):
    admin = login(client, "admin@seagullsdemo.com", "Admin123!")
    closer = login(client, "closer@seagullsdemo.com", "Closer123!")
    agent = login(client, "agent@seagullsdemo.com", "Agent123!")

    agents = client.get("/api/agents", headers=auth(closer)).json()
    campaigns = client.get("/api/campaigns", headers=auth(closer)).json()
    create = client.post(
        "/api/leads",
        headers=auth(closer),
        json={
            "customer_number": "CUST-100",
            "first_name": "Test",
            "last_name": "Customer",
            "state": "TX",
            "zip_code": "75001",
            "agent_id": agents[0]["id"],
            "campaign_id": campaigns[0]["id"],
            "did": "5551234567",
            "d1": "D1-A",
            "other": None,
            "comments": "Test lead",
        },
    )
    assert create.status_code == 201, create.text
    lead = create.json()
    assert lead["initial_status"] == "Pending"
    assert lead["buyer_response"] == "Pending / Not Received"
    assert lead["final_status"] == "Pending"

    forbidden_put = client.put(
        f"/api/leads/{lead['id']}",
        headers=auth(agent),
        json={"final_status": "Accepted"},
    )
    assert forbidden_put.status_code == 403

    forbidden_del = client.delete(f"/api/leads/{lead['id']}", headers=auth(agent))
    assert forbidden_del.status_code == 403

    closer_edit = client.patch(
        f"/api/leads/{lead['id']}",
        headers=auth(closer),
        json={"final_status": "Accepted"},
    )
    assert closer_edit.status_code == 403

    closer_del = client.delete(f"/api/leads/{lead['id']}", headers=auth(closer))
    assert closer_del.status_code == 403

    admin_update = client.patch(
        f"/api/leads/{lead['id']}",
        headers=auth(admin),
        json={"buyer_response": "Accepted", "final_status": "Accepted"},
    )
    assert admin_update.status_code == 200, admin_update.text
    assert admin_update.json()["final_status"] == "Accepted"

    dash = client.get("/api/dashboard", headers=auth(admin)).json()
    assert dash["summary"]["accepted"] >= 1
    assert dash["summary"]["total_leads"] == (
        dash["summary"]["accepted"] + dash["summary"]["rejected"] + dash["summary"]["pending"]
    )


def test_rejection_requires_reason(client):
    admin = login(client, "admin@seagullsdemo.com", "Admin123!")
    closer = login(client, "closer@seagullsdemo.com", "Closer123!")
    agents = client.get("/api/agents", headers=auth(closer)).json()
    campaigns = client.get("/api/campaigns", headers=auth(closer)).json()
    create = client.post(
        "/api/leads",
        headers=auth(closer),
        json={
            "customer_number": "CUST-200",
            "first_name": "Reject",
            "last_name": "Me",
            "state": "CA",
            "zip_code": "90001",
            "agent_id": agents[0]["id"],
            "campaign_id": campaigns[0]["id"],
            "did": "5559876543",
        },
    )
    lead_id = create.json()["id"]
    bad = client.patch(
        f"/api/leads/{lead_id}",
        headers=auth(admin),
        json={"buyer_response": "Rejected", "final_status": "Rejected"},
    )
    assert bad.status_code == 422
    assert "rejection reason" in bad.json()["detail"].lower()

    # Frontend-style payload with explicit null reason must also fail and not persist.
    bad_null = client.patch(
        f"/api/leads/{lead_id}",
        headers=auth(admin),
        json={
            "buyer_response": "Rejected",
            "final_status": "Rejected",
            "rejection_reason": None,
        },
    )
    assert bad_null.status_code == 422
    still_pending = client.get(f"/api/leads/{lead_id}", headers=auth(admin)).json()
    assert still_pending["final_status"] == "Pending"
    assert still_pending["rejection_reason"] is None

    good = client.patch(
        f"/api/leads/{lead_id}",
        headers=auth(admin),
        json={
            "buyer_response": "Rejected",
            "final_status": "Rejected",
            "rejection_reason": "Duplicate Lead",
        },
    )
    assert good.status_code == 200
    assert good.json()["final_status"] == "Rejected"
    assert good.json()["buyer_response"] == "Rejected"
    assert good.json()["rejection_reason"] == "Duplicate Lead"

    fetched = client.get(f"/api/leads/{lead_id}", headers=auth(admin)).json()
    assert fetched["final_status"] == "Rejected"
    assert fetched["buyer_response"] == "Rejected"
    assert fetched["rejection_reason"] == "Duplicate Lead"


def test_pending_to_rejected_persists_and_updates_dashboard(client):
    admin = login(client, "admin@seagullsdemo.com", "Admin123!")
    closer = login(client, "closer@seagullsdemo.com", "Closer123!")
    agents = client.get("/api/agents", headers=auth(closer)).json()
    campaigns = client.get("/api/campaigns", headers=auth(closer)).json()

    before = client.get("/api/dashboard", headers=auth(admin)).json()["summary"]

    create = client.post(
        "/api/leads",
        headers=auth(closer),
        json={
            "customer_number": "CUST-REJ-PERSIST",
            "first_name": "Persist",
            "last_name": "Reject",
            "state": "TX",
            "zip_code": "75001",
            "agent_id": agents[0]["id"],
            "campaign_id": campaigns[0]["id"],
            "did": "5550001111",
            "d1": None,
            "other": None,
            "comments": "regression",
        },
    )
    assert create.status_code == 201
    lead = create.json()
    assert lead["final_status"] == "Pending"

    # Exact shape sent by the Admin lead editor.
    payload = {
        "customer_number": lead["customer_number"],
        "first_name": lead["first_name"],
        "last_name": lead["last_name"],
        "state": lead["state"],
        "zip_code": lead["zip_code"],
        "agent_id": lead["agent_id"],
        "closer_id": lead["closer_id"],
        "campaign_id": lead["campaign_id"],
        "did": lead["did"],
        "d1": None,
        "other": None,
        "comments": "regression",
        "buyer_response": "Rejected",
        "final_status": "Rejected",
        "rejection_reason": "Invalid Phone",
        "admin_notes": "Rejected in regression test",
    }
    updated = client.patch(f"/api/leads/{lead['id']}", headers=auth(admin), json=payload)
    assert updated.status_code == 200, updated.text
    body = updated.json()
    assert body["initial_status"] == "Pending"
    assert body["buyer_response"] == "Rejected"
    assert body["final_status"] == "Rejected"
    assert body["rejection_reason"] == "Invalid Phone"
    assert body["finalized_at"] is not None

    fetched = client.get(f"/api/leads/{lead['id']}", headers=auth(admin)).json()
    assert fetched["final_status"] == "Rejected"
    assert fetched["buyer_response"] == "Rejected"
    assert fetched["rejection_reason"] == "Invalid Phone"

    after = client.get("/api/dashboard", headers=auth(admin)).json()["summary"]
    assert after["total_leads"] == before["total_leads"] + 1
    assert after["rejected"] == before["rejected"] + 1
    assert after["pending"] == before["pending"]  # new lead moved out of pending
    assert after["total_leads"] == after["accepted"] + after["rejected"] + after["pending"]

    audit = client.get("/api/audit", headers=auth(admin), params={"search": str(lead["lead_number"])}).json()
    actions = {item["action"] for item in audit["items"]}
    assert "Final Status Changed" in actions
    assert "Rejection Reason Changed" in actions


def test_all_rejection_reasons_persist(client):
    from app.core.constants import RejectionReason

    admin = login(client, "admin@seagullsdemo.com", "Admin123!")
    closer = login(client, "closer@seagullsdemo.com", "Closer123!")
    agents = client.get("/api/agents", headers=auth(closer)).json()
    campaigns = client.get("/api/campaigns", headers=auth(closer)).json()

    for idx, reason in enumerate(RejectionReason):
        create = client.post(
            "/api/leads",
            headers=auth(closer),
            json={
                "customer_number": f"CUST-RR-{idx}",
                "first_name": "Reason",
                "last_name": f"Case{idx}",
                "state": "NY",
                "zip_code": "10001",
                "agent_id": agents[0]["id"],
                "campaign_id": campaigns[0]["id"],
                "did": f"555100{idx:04d}",
            },
        )
        assert create.status_code == 201
        lead_id = create.json()["id"]
        res = client.patch(
            f"/api/leads/{lead_id}",
            headers=auth(admin),
            json={
                "buyer_response": "Rejected",
                "final_status": "Rejected",
                "rejection_reason": reason.value,
            },
        )
        assert res.status_code == 200, res.text
        fetched = client.get(f"/api/leads/{lead_id}", headers=auth(admin)).json()
        assert fetched["final_status"] == "Rejected"
        assert fetched["buyer_response"] == "Rejected"
        assert fetched["rejection_reason"] == reason.value


def test_pending_to_accepted_still_works(client):
    admin = login(client, "admin@seagullsdemo.com", "Admin123!")
    closer = login(client, "closer@seagullsdemo.com", "Closer123!")
    agents = client.get("/api/agents", headers=auth(closer)).json()
    campaigns = client.get("/api/campaigns", headers=auth(closer)).json()
    create = client.post(
        "/api/leads",
        headers=auth(closer),
        json={
            "customer_number": "CUST-ACC-PERSIST",
            "first_name": "Accept",
            "last_name": "Me",
            "state": "WA",
            "zip_code": "98101",
            "agent_id": agents[0]["id"],
            "campaign_id": campaigns[0]["id"],
            "did": "5552223333",
        },
    )
    lead_id = create.json()["id"]
    res = client.patch(
        f"/api/leads/{lead_id}",
        headers=auth(admin),
        json={
            "buyer_response": "Accepted",
            "final_status": "Accepted",
            "rejection_reason": None,
        },
    )
    assert res.status_code == 200
    fetched = client.get(f"/api/leads/{lead_id}", headers=auth(admin)).json()
    assert fetched["final_status"] == "Accepted"
    assert fetched["buyer_response"] == "Accepted"
    assert fetched["rejection_reason"] is None


def test_filters_and_export_and_audit(client):
    admin = login(client, "admin@seagullsdemo.com", "Admin123!")
    leads = client.get("/api/leads", headers=auth(admin), params={"final_status": "Accepted"})
    assert leads.status_code == 200
    csv_res = client.get("/api/reports/export", headers=auth(admin), params={"format": "csv"})
    assert csv_res.status_code == 200
    assert "Lead ID" in csv_res.text
    xlsx = client.get("/api/reports/export", headers=auth(admin), params={"format": "xlsx"})
    assert xlsx.status_code == 200
    assert xlsx.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    audit = client.get("/api/audit", headers=auth(admin))
    assert audit.status_code == 200
    assert audit.json()["total"] >= 1

    agent = login(client, "agent@seagullsdemo.com", "Agent123!")
    assert client.get("/api/audit", headers=auth(agent)).status_code == 403


def test_agent_cannot_submit_form(client):
    agent = login(client, "agent@seagullsdemo.com", "Agent123!")
    agents = client.get("/api/agents", headers=auth(agent)).json()
    campaigns = client.get("/api/campaigns", headers=auth(agent)).json()
    res = client.post(
        "/api/leads",
        headers=auth(agent),
        json={
            "customer_number": "X",
            "first_name": "A",
            "last_name": "B",
            "state": "NY",
            "zip_code": "10001",
            "agent_id": agents[0]["id"],
            "campaign_id": campaigns[0]["id"],
            "did": "1",
        },
    )
    assert res.status_code == 403


def test_logout(client):
    token = login(client, "admin@seagullsdemo.com", "Admin123!")
    res = client.post("/api/auth/logout", headers=auth(token))
    assert res.status_code == 200
