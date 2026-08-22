import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal, engine, Base
from app.models.user import User
from app.models.ticket import Event
from app.models.ticket_tier import TicketTier
from app.core.security import get_password_hash, create_access_token

@pytest.fixture(autouse=True)
def setup_manual_event_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    org = User(id=1, email="organizer@test.com", name="Test Organizer", hashed_password=get_password_hash("pass"), role="organizer")
    cust = User(id=2, email="student@test.com", name="Test Student", hashed_password=get_password_hash("pass"), role="customer")
    db.add_all([org, cust])
    db.commit()
    db.close()

def test_required_manual_event_acceptance_flow():
    """
    Acceptance Test (Requirement 8):
    Create organizer -> Login -> Create 'My College Tech Fest' event -> Publish -> Verify DB & API
    """
    client = TestClient(app)
    org_token = create_access_token(data={"sub": "1", "role": "organizer"})
    headers = {"Authorization": f"Bearer {org_token}"}

    # 1. Create Event via HTTP API
    create_payload = {
        "title": "My College Tech Fest",
        "description": "Annual technology fest for engineering students.",
        "category": "Technology",
        "venue": "AJIET Main Auditorium",
        "location": "Mangaluru",
        "date_str": "2026-09-30",
        "start_time": "09:30",
        "end_time": "16:30",
        "price": 299.0,
        "total_capacity": 150,
        "max_tickets_per_booking": 5,
        "status": "DRAFT",
        "ticket_types": [
            {
                "name": "General",
                "price": 299.0,
                "total_quantity": 150,
                "min_per_order": 1,
                "max_per_order": 5
            }
        ]
    }

    res = client.post("/api/v1/events", json=create_payload, headers=headers)
    assert res.status_code == 200, res.text
    event_id = res.json()["id"]

    # 2. Publish Event via HTTP API
    pub_res = client.post(f"/api/v1/events/{event_id}/publish", headers=headers)
    assert pub_res.status_code == 200, pub_res.text

    # 3. Direct DB Inspection & Invariants Verification
    db = SessionLocal()
    db_ev = db.query(Event).filter(Event.id == event_id).first()
    assert db_ev is not None
    assert db_ev.status == "PUBLISHED"
    assert db_ev.price == 299.0
    assert db_ev.total_capacity == 150
    assert db_ev.available_tickets == 150
    assert db_ev.max_tickets_per_booking == 5

    tiers = db.query(TicketTier).filter(TicketTier.event_id == event_id).all()
    assert len(tiers) == 1
    tier = tiers[0]

    assert tier.name == "General"
    assert tier.price == 299.0
    assert tier.total_quantity == 150
    assert tier.available_quantity == 150
    assert tier.held_quantity == 0
    assert tier.sold_quantity == 0
    assert tier.max_per_order == 5

    db.close()

    # 4. Public API Discovery Verification
    events_res = client.get("/api/v1/events")
    assert events_res.status_code == 200
    events_data = events_res.json()
    assert any(e["id"] == event_id and e["title"] == "My College Tech Fest" for e in events_data)
