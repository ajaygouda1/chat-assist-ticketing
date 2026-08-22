import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal, engine, Base
from app.models.user import User
from app.models.ticket import Event
from app.models.ticket_tier import TicketTier
from app.core.security import get_password_hash

@pytest.fixture(autouse=True)
def setup_api_e2e_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    org = User(id=1, email="organizer@test.com", name="Test Organizer", hashed_password=get_password_hash("pass"), role="organizer")
    db.add(org)
    db.commit()
    db.close()

def test_complete_end_to_end_event_creation_api_flow():
    """
    Simulates the exact EventWizard 5-Step & Discovery flow:
    1. Create Draft Event (Step 1-4)
    2. Add General (100 @ 499) + VIP (25 @ 999) Tiers
    3. Publish Event (Step 5)
    4. Query published events in DB (Explore Page)
    5. Verify Event & Ticket Tiers in DB
    """
    db = SessionLocal()

    # 1. Create Draft Event
    draft_event = Event(
        title="CodeFest 2026",
        description="Coding and AI workshop for engineering students.",
        category="Technology",
        location="Mangaluru",
        venue="AJIET",
        date_str="25 September 2026",
        start_time="10:00",
        end_time="16:00",
        price=499.0,
        total_capacity=125,
        available_tickets=125,
        organizer_id=1,
        status="DRAFT"
    )
    db.add(draft_event)
    db.commit()
    db.refresh(draft_event)
    assert draft_event.status == "DRAFT"

    # 2. Attach Tiers
    tiers_payload = [
        {"name": "General", "price": 499.0, "total_quantity": 100, "min_per_order": 1, "max_per_order": 5},
        {"name": "VIP", "price": 999.0, "total_quantity": 25, "min_per_order": 1, "max_per_order": 2}
    ]
    from app.services.tier_inventory_service import create_or_update_event_tiers
    tiers = create_or_update_event_tiers(db, draft_event, tiers_payload)
    assert len(tiers) == 2

    # 3. Publish Event
    from app.services.event_lifecycle import transition_event_status
    transition_event_status(draft_event, "PUBLISHED")
    db.commit()
    assert draft_event.status == "PUBLISHED"

    # 4. Explore Query Verification
    published_events = db.query(Event).filter(Event.status == "PUBLISHED", Event.title.ilike("%CodeFest%")).all()
    assert len(published_events) == 1
    found = published_events[0]

    assert found.title == "CodeFest 2026"
    assert found.location == "Mangaluru"
    assert found.venue == "AJIET"
    assert found.total_capacity == 125

    # 5. Ticket Tier Stock Verification
    db_tiers = db.query(TicketTier).filter(TicketTier.event_id == found.id).all()
    assert len(db_tiers) == 2

    gen_tier = next(t for t in db_tiers if t.name == "General")
    vip_tier = next(t for t in db_tiers if t.name == "VIP")

    assert gen_tier.total_quantity == 100
    assert gen_tier.available_quantity == 100
    assert gen_tier.price == 499.0

    assert vip_tier.total_quantity == 25
    assert vip_tier.available_quantity == 25
    assert vip_tier.price == 999.0

    db.close()

