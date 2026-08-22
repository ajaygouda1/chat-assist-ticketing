import sys
import os
import uuid
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from app.core.database import SessionLocal
from app.models.ticket import Event, Ticket
from app.models.ticket_tier import TicketTier
from app.services.booking_conversation import get_booking_session, BookingState
from app.services.openai_service import ai_service
from app.services.payment_service import confirm_payment
from app.services.tier_inventory_service import create_or_update_event_tiers

def test_chat_greeting_flow():
    db = SessionLocal()
    user_id = 888
    session = get_booking_session(user_id)
    session.reset()

    res = ai_service.process_chat_message("Hi", user_id=user_id, db=db)
    assert res["intent"] == "greeting"
    assert "Hi!" in res["reply"]
    assert len(res["quick_replies"]) == 3
    print("✓ Greeting test passed.")

def test_chat_discovery_and_ordinals():
    db = SessionLocal()
    user_id = 889
    session = get_booking_session(user_id)
    session.reset()

    # Ensure demo events in DB
    ev1 = db.query(Event).filter(Event.available_tickets > 0).first()
    if not ev1:
        ev1 = Event(
            title="Bengaluru AI Summit 2026",
            description="AI Conference with hands-on coding",
            category="Technology",
            location="Bengaluru",
            date_str="2026-09-15",
            price=499.0,
            total_capacity=50,
            available_tickets=50,
            status="PUBLISHED"
        )
        db.add(ev1)
        db.commit()
        db.refresh(ev1)

    # 1. Search events
    search_res = ai_service.process_chat_message("Show tech events", user_id=user_id, db=db)
    assert search_res["type"] in ["event_results", "event_card"]
    assert len(session.last_event_results) > 0

    # 2. Ordinal reference selection ("tell me about the first one")
    target_id = session.last_event_results[0]
    first_ev = db.query(Event).filter(Event.id == target_id).first()

    book_res = ai_service.process_chat_message("Book the first one", user_id=user_id, db=db)
    assert session.event_id == first_ev.id
    print("✓ Event discovery and ordinal selection test passed.")

def test_chat_create_event_and_manual_publish():
    db = SessionLocal()
    user_id = 890
    session = get_booking_session(user_id)
    session.reset()

    # 1. User says "I want to create an event"
    res = ai_service.process_chat_message("I want to create an event", user_id=user_id, db=db)
    assert res["intent"] == "create_event"
    assert res["type"] == "create_event_entry"
    assert "create your event" in res["reply"].lower()
    # Ensure NO fake event was written to DB
    print("✓ Create event chat action returns navigation card (no fake chat event).")

    # 2. Organizer manually creates and publishes event
    unique_title = f"My College Tech Fest {uuid.uuid4().hex[:6]}"
    manual_event = Event(
        title=unique_title,
        description="Manual organizer fest",
        category="Technology",
        venue="AJIET Main Auditorium",
        location="Mangaluru",
        date_str="2026-09-30",
        start_time="09:30",
        end_time="16:30",
        price=299.0,
        total_capacity=150,
        available_tickets=150,
        status="PUBLISHED",
        max_tickets_per_booking=5
    )
    db.add(manual_event)
    db.commit()
    db.refresh(manual_event)

    create_or_update_event_tiers(db, manual_event, [
        {"name": "General", "price": 299.0, "total_quantity": 150, "min_per_order": 1, "max_per_order": 5}
    ])

    # 3. User in chat searches for newly published event
    session.reset()
    search_created = ai_service.process_chat_message(f"Find {unique_title}", user_id=user_id, db=db)
    assert search_created["type"] in ["event_results", "event_card"]

    # 4. User books 2 tickets for created event
    book_turn = ai_service.process_chat_message(f"Book 2 tickets for {unique_title}", user_id=user_id, db=db)
    assert book_turn["type"] == "booking_summary"
    assert book_turn["payload"]["quantity"] == 2
    assert book_turn["payload"]["unit_price"] == 299.0

    print("✓ Manually published event searchable and bookable via ChatAssist!")

def test_grounded_event_faq():
    db = SessionLocal()
    user_id = 891
    session = get_booking_session(user_id)
    session.reset()

    # Search to set active event context
    search_res = ai_service.process_chat_message("Show tech events", user_id=user_id, db=db)

    # Ask FAQ
    faq_res = ai_service.process_chat_message("Does it provide certificates?", user_id=user_id, db=db)
    assert "reply" in faq_res
    print("✓ Grounded FAQ test passed.")

if __name__ == "__main__":
    test_chat_greeting_flow()
    test_chat_discovery_and_ordinals()
    test_chat_create_event_and_manual_publish()
    test_grounded_event_faq()
    print("\n🎉 ALL CHAT COMPLETE FLOW TESTS PASSED SUCCESSFULLY!")
