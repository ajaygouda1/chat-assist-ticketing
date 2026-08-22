import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from app.core.database import SessionLocal, engine, Base
from app.models.user import User
from app.models.ticket import Event, Ticket
from app.models.ticket_tier import TicketTier
from app.services.tier_inventory_service import create_or_update_event_tiers, hold_tier_inventory, confirm_tier_inventory_payment

from app.core.security import get_password_hash
from app.services.event_lifecycle import transition_event_status

@pytest.fixture(autouse=True)
def setup_manual_event_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    org = User(id=1, email="organizer@test.com", name="Test Organizer", hashed_password=get_password_hash("pass"), role="organizer")
    cust = User(id=2, email="student@test.com", name="Test Student", hashed_password=get_password_hash("pass"), role="user")
    db.add_all([org, cust])
    db.commit()
    db.close()

def test_required_manual_event_and_booking_inventory_flow():
    """
    Validates Item 44, 45, and 46 of the User Specification:
    Event: My College Tech Fest
    Venue: AJIET Main Auditorium, Mangaluru
    Date: 30 September 2026 (09:30 - 16:30)
    Pricing: ₹299, Quantity: 150, Max per person: 5
    """
    db = SessionLocal()

    # 1. Create Event
    ev = Event(
        title="My College Tech Fest",
        description="Annual technology fest for engineering students.",
        category="Technology",
        location="Mangaluru",
        venue="AJIET Main Auditorium",
        date_str="2026-09-30",
        start_time="09:30",
        end_time="16:30",
        price=299.0,
        total_capacity=150,
        available_tickets=150,
        organizer_id=1,
        status="DRAFT"
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)

    # 2. Attach General TicketTier (150 @ ₹299, max_per_order = 5)
    tiers_payload = [
        {"name": "General", "price": 299.0, "total_quantity": 150, "min_per_order": 1, "max_per_order": 5}
    ]
    tiers = create_or_update_event_tiers(db, ev, tiers_payload)
    assert len(tiers) == 1

    gen_tier = tiers[0]
    assert gen_tier.name == "General"
    assert gen_tier.price == 299.0
    assert gen_tier.total_quantity == 150
    assert gen_tier.available_quantity == 150
    assert gen_tier.held_quantity == 0
    assert gen_tier.sold_quantity == 0

    # 3. Publish Event
    transition_event_status(ev, "PUBLISHED")
    db.commit()
    assert ev.status == "PUBLISHED"

    # 4. Explore Discovery Query
    published_events = db.query(Event).filter(Event.status == "PUBLISHED", Event.title.ilike("%My College Tech Fest%")).all()
    assert len(published_events) == 1
    found = published_events[0]

    assert found.title == "My College Tech Fest"
    assert found.venue == "AJIET Main Auditorium"
    assert found.location == "Mangaluru"
    assert found.price == 299.0
    assert found.total_capacity == 150

    # 5. Customer Books 2 Tickets (Hold -> Confirm Payment)
    held_tier = hold_tier_inventory(db, ev.id, gen_tier.id, requested_qty=2, user_id=2)
    assert held_tier is not None

    db.refresh(gen_tier)
    assert gen_tier.available_quantity == 148
    assert gen_tier.held_quantity == 2
    assert gen_tier.sold_quantity == 0

    # Confirm Payment
    confirm_tier_inventory_payment(db, ev.id, gen_tier.id, qty=2)
    db.refresh(gen_tier)
    assert gen_tier.available_quantity == 148
    assert gen_tier.held_quantity == 0
    assert gen_tier.sold_quantity == 2


    # Invariant Check: TOTAL = AVAILABLE + HELD + SOLD
    assert gen_tier.total_quantity == gen_tier.available_quantity + gen_tier.held_quantity + gen_tier.sold_quantity

    db.close()
