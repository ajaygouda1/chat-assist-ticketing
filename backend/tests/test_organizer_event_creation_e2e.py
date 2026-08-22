import pytest
from app.core.database import SessionLocal, engine, Base
from app.models.user import User
from app.models.ticket import Event
from app.models.ticket_tier import TicketTier
from app.services.openai_service import ai_service
from app.ml.slot_extractor import extract_event_slots
from app.services.tier_inventory_service import create_or_update_event_tiers
from app.core.security import get_password_hash

@pytest.fixture(autouse=True)
def setup_e2e_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    org = User(id=1, email="organizer@test.com", name="Test Organizer", hashed_password=get_password_hash("pass"), role="organizer")
    db.add(org)
    db.commit()
    db.close()

def test_1_slot_extractor_never_invents_details():
    """1. Slot extractor returns None for missing fields without inventing fake dates or locations"""
    slots = extract_event_slots("I want to create a tech workshop event")

    assert slots["category"] == "Technology"
    assert slots["event_type"] == "Workshop"

    # Must NOT invent date, venue, or price!
    assert slots["title"] is None
    assert slots["date"] is None
    assert slots["venue"] is None
    assert slots["price"] is None

def test_2_chat_create_event_intent_returns_entry_card():
    """2. AI Chat returns type create_event_entry without inventing details or publishing automatically"""
    db = SessionLocal()
    res = ai_service.process_chat_message("I want to organize a tech workshop in Mangaluru", user_id=1, db=db)

    assert res["intent"] == "create_event"
    assert res["type"] == "create_event_entry"
    assert res["payload"]["category"] == "Technology"
    assert res["payload"]["event_type"] == "Workshop"
    assert res["payload"]["city"] == "Mangaluru"
    assert res["payload"]["title"] is None  # Not invented!

    assert len(res["quick_replies"]) > 0
    assert any("Create Event" in qr["label"] or "Start Event Setup" in qr["label"] for qr in res["quick_replies"])

    db.close()

def test_3_event_wizard_draft_and_publish_flow():
    """3. End-to-End EventWizard creation, draft saving, publishing, and live inventory verification"""
    db = SessionLocal()

    # Step A: Save Draft
    draft_event = Event(
        title="CodeFest 2026",
        description="Official CodeFest 2026 Hackathon in Mangaluru",
        category="Technology",
        location="Mangaluru",
        venue="AJIET",
        date_str="25 September 2026",
        price=499.0,
        total_capacity=125,
        available_tickets=125,
        organizer_id=1,
        status="DRAFT"
    )
    db.add(draft_event)
    db.commit()
    db.refresh(draft_event)

    # Attach Tier Inventories (General: 100, VIP: 25)
    tiers_payload = [
        {"name": "General Pass", "price": 499.0, "total_quantity": 100, "min_per_order": 1, "max_per_order": 5},
        {"name": "VIP Pass", "price": 999.0, "total_quantity": 25, "min_per_order": 1, "max_per_order": 4}
    ]
    tiers = create_or_update_event_tiers(db, draft_event, tiers_payload)
    assert len(tiers) == 2

    # Verify Draft Status
    assert draft_event.status == "DRAFT"

    # Step B: Publish Event
    from app.services.event_lifecycle import transition_event_status
    transition_event_status(draft_event, "PUBLISHED")
    db.commit()
    assert draft_event.status == "PUBLISHED"


    # Step C: Discovery & Inventory Verification
    live_events = db.query(Event).filter(Event.status == "PUBLISHED", Event.title.ilike("%CodeFest%")).all()
    assert len(live_events) == 1
    found = live_events[0]

    event_tiers = db.query(TicketTier).filter(TicketTier.event_id == found.id).all()
    assert len(event_tiers) == 2

    gen_tier = next(t for t in event_tiers if t.name == "General Pass")
    vip_tier = next(t for t in event_tiers if t.name == "VIP Pass")

    assert gen_tier.total_quantity == 100
    assert gen_tier.available_quantity == 100
    assert gen_tier.sold_quantity == 0
    assert gen_tier.held_quantity == 0

    assert vip_tier.total_quantity == 25
    assert vip_tier.available_quantity == 25
    assert vip_tier.sold_quantity == 0
    assert vip_tier.held_quantity == 0

    # Total Capacity Parity
    assert found.total_capacity == 125
    assert found.available_tickets == 125
    db.close()
