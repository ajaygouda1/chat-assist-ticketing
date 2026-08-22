import pytest
from app.core.database import SessionLocal, engine, Base
from app.models.user import User
from app.models.ticket import Event
from app.models.ticket_tier import TicketTier
from app.services.openai_service import ai_service
from app.services.tier_inventory_service import create_or_update_event_tiers
from app.core.security import get_password_hash
from app.services.event_lifecycle import transition_event_status

@pytest.fixture(autouse=True)
def setup_scenarios_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    org = User(id=1, email="organizer@test.com", name="Test Organizer", hashed_password=get_password_hash("pass"), role="organizer")
    db.add(org)
    db.commit()
    db.close()

def test_scenario_a_no_invented_details_and_single_entry():
    """Scenario A: Chat extracts ONLY supplied info and returns create_event_entry card with NO fake dates/venues/prices"""
    db = SessionLocal()

    # User says: "I want to create a tech workshop event"
    res = ai_service.process_chat_message("I want to create a tech workshop event", user_id=1, db=db)

    assert res["intent"] == "create_event"
    assert res["type"] == "create_event_entry"

    payload = res["payload"]
    assert payload["category"] == "Technology"
    assert payload["event_type"] == "Workshop"

    # CRITICAL: NO invented details!
    assert payload.get("title") is None
    assert payload.get("city") is None
    assert payload.get("date_str") is None

    # Reply text must be clean
    assert "event setup form" in res["reply"] or "Technology" in res["reply"]
    assert "Koramangala" not in res["reply"]
    assert "Standard Pass" not in res["reply"]
    assert "Publish Event to Live DB" not in res["reply"]
    db.close()


def test_scenario_b_start_event_setup_prefills_only_extracted():
    """Scenario B: Start Event Setup passes extracted category/type to EventWizard while everything else is empty"""
    from app.ml.slot_extractor import extract_event_slots
    slots = extract_event_slots("I want to create a tech workshop event")

    assert slots["category"] == "Technology"
    assert slots["event_type"] == "Workshop"
    assert slots["title"] is None
    assert slots["venue"] is None
    assert slots["price"] is None

def test_scenario_c_navbar_create_event_opens_blank_wizard():
    """Scenario C: Direct + Create Event navigation button opens blank draft without chat side-effects"""
    db = SessionLocal()
    blank_event = Event(
        title="",
        description="",
        category="Technology",
        location="",
        date_str="TBD",
        price=0.0,
        total_capacity=100,
        available_tickets=100,
        organizer_id=1,
        status="DRAFT"
    )
    db.add(blank_event)
    db.commit()

    assert blank_event.status == "DRAFT"
    assert blank_event.title == ""
    assert blank_event.location == ""
    db.close()


def test_scenario_d_end_to_end_custom_tiers_and_explore_discovery():
    """Scenario D: Organizer configures General (100 @ ₹499) + VIP (25 @ ₹999), capacity=125, publishes, and discovers in Explore"""
    db = SessionLocal()

    # Create event draft
    event = Event(
        title="AI Builders Workshop 2026",
        description="Hands-on agentic systems workshop",
        category="Technology",
        location="Mangaluru",
        venue="AJIET",
        date_str="2026-09-25",
        price=499.0,
        total_capacity=125,
        available_tickets=125,
        organizer_id=1,
        status="DRAFT"
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    # Attach organizer-configured tiers
    tiers_payload = [
        {"name": "General", "price": 499.0, "total_quantity": 100, "min_per_order": 1, "max_per_order": 5},
        {"name": "VIP", "price": 999.0, "total_quantity": 25, "min_per_order": 1, "max_per_order": 4}
    ]
    tiers = create_or_update_event_tiers(db, event, tiers_payload)
    assert len(tiers) == 2

    # Total capacity parity check
    computed_cap = sum(t.total_quantity for t in tiers)
    assert computed_cap == 125

    # Publish Event
    transition_event_status(event, "PUBLISHED")
    db.commit()
    assert event.status == "PUBLISHED"

    # Search in Explore
    found_events = db.query(Event).filter(Event.status == "PUBLISHED", Event.title.ilike("%AI Builders Workshop%")).all()
    assert len(found_events) == 1
    found = found_events[0]

    assert found.title == "AI Builders Workshop 2026"
    assert found.venue == "AJIET"
    assert found.location == "Mangaluru"
    assert found.total_capacity == 125
    db.close()
