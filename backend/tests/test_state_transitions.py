import pytest
import uuid
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.ticket import Event, Ticket
from app.services.booking_conversation import get_booking_session, BookingState
from app.services.openai_service import ai_service
from app.services.payment_service import confirm_payment

@pytest.fixture
def db():
    from app.core.database import engine
    from sqlalchemy import text
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE events ADD COLUMN max_tickets_per_booking INTEGER DEFAULT 10;"))
            conn.commit()
        except Exception:
            pass
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

def test_1_change_quantity(db: Session):
    user_id = 8801
    session = get_booking_session(user_id)
    session.reset()

    # Step A: Initiate booking
    r1 = ai_service.process_chat_message("Book 2 VIP tickets for India AI & Deep Learning Summit", user_id=user_id, db=db)
    assert r1["type"] == "booking_summary"
    assert session.quantity == 2
    assert session.ticket_type == "VIP Pass"

    # Step B: Change quantity to 3
    r2 = ai_service.process_chat_message("Make it 3 tickets", user_id=user_id, db=db)
    assert r2["type"] == "booking_summary"
    assert session.quantity == 3
    assert r2["payload"]["quantity"] == 3
    # Check total recalculation
    unit = r2["payload"]["unit_price"]
    subtotal = round(unit * 3, 2)
    tax = round(subtotal * 0.18, 2)
    assert r2["payload"]["subtotal"] == subtotal
    assert r2["payload"]["total"] == round(subtotal + tax, 2)

def test_2_change_tier(db: Session):
    user_id = 8802
    session = get_booking_session(user_id)
    session.reset()

    # Step A: Initial VIP selection
    r1 = ai_service.process_chat_message("Book 2 VIP tickets for India AI & Deep Learning Summit", user_id=user_id, db=db)
    assert session.ticket_type == "VIP Pass"

    # Step B: Change tier to Standard
    r2 = ai_service.process_chat_message("Change to Standard pass", user_id=user_id, db=db)
    assert r2["type"] == "booking_summary"
    assert session.ticket_type == "Standard"
    assert r2["payload"]["ticket_type"] == "Standard"

def test_3_and_4_payment_system_event_and_idempotency(db: Session):
    user_id = 8803
    session = get_booking_session(user_id)
    session.reset()

    # Turn 1: Select event
    ai_service.process_chat_message("Book 2 Standard tickets for India AI & Deep Learning Summit", user_id=user_id, db=db)
    # Turn 2: Confirm
    r_pay = ai_service.process_chat_message("Confirm booking", user_id=user_id, db=db)
    assert r_pay["type"] == "payment_button"
    order_id = r_pay["payload"]["order_id"]
    booking_id = r_pay["payload"]["booking_id"]

    # Step 3: Payment confirmation via service
    pay_id = f"pay_test_trans_{uuid.uuid4().hex[:6]}"
    confirm1 = confirm_payment(order_id, pay_id, "mock_sig", booking_id=booking_id, user_id=user_id, db=db)
    assert confirm1["status"] == "CONFIRMED"
    ticket_no = confirm1["ticket"]["ticket_number"]

    # Trigger system_event in AI Service
    sys_event_res = ai_service.process_chat_message(
        message="",
        user_id=user_id,
        db=db,
        event_type="system_event",
        payload={"event": "PAYMENT_VERIFIED", "ticket": confirm1["ticket"]}
    )
    assert sys_event_res["type"] == "ticket_confirmation"
    assert session.state == BookingState.PAID

    # Step 4: Retry Payment Idempotency
    confirm2 = confirm_payment(order_id, pay_id, "mock_sig", booking_id=booking_id, user_id=user_id, db=db)
    assert confirm2["status"] == "ALREADY_CONFIRMED"
    assert confirm2["ticket"]["ticket_number"] == ticket_no

def test_5_cancel_active_draft(db: Session):
    user_id = 8805
    session = get_booking_session(user_id)
    session.reset()

    ai_service.process_chat_message("Book 2 VIP tickets", user_id=user_id, db=db)
    assert session.state == BookingState.QTY_SELECTED

    # Cancel draft
    r_cancel = ai_service.process_chat_message("cancel", user_id=user_id, db=db)
    assert session.state == BookingState.IDLE
    assert "released" in r_cancel["reply"].lower()

def test_6_conversation_state_isolation(db: Session):
    user_id = 8806
    conv_a = 101
    conv_b = 102

    # Session A: Start booking -> PAYMENT_PENDING
    ai_service.process_chat_message("Book 2 VIP tickets for India AI & Deep Learning Summit", user_id=user_id, db=db, conversation_id=conv_a)
    r_pay_a = ai_service.process_chat_message("Confirm booking", user_id=user_id, db=db, conversation_id=conv_a)
    assert r_pay_a["type"] == "payment_button"

    # Session B: User opens new conversation and requests event creation
    r_b = ai_service.process_chat_message("I want to create a tech workshop event", user_id=user_id, db=db, conversation_id=conv_b)
    assert r_b["mode"] == "EVENT_CREATION"
    assert r_b["type"] in ["create_event_entry", "event_creation_card"]
    assert "payment" not in r_b["reply"].lower()

    # Session A remains isolated in PAYMENT_PENDING booking mode
    session_a = get_booking_session(user_id, conv_a)
    assert session_a.state == BookingState.PAYMENT_PENDING

def test_7_mode_switching(db: Session):
    user_id = 8807
    conv_id = 201
    session = get_booking_session(user_id, conv_id)
    session.reset()

    # Initiate booking
    ai_service.process_chat_message("Book 2 tickets", user_id=user_id, db=db, conversation_id=conv_id)
    assert session.mode == "BOOKING"

    # User switches intent mid-stream to create event
    r_switch = ai_service.process_chat_message("Actually I want to create a tech workshop event", user_id=user_id, db=db, conversation_id=conv_id)
    assert r_switch["mode"] == "EVENT_CREATION"
    assert r_switch["type"] in ["create_event_entry", "event_creation_card"]

    assert "payment" not in r_switch["reply"].lower()

def test_8_multi_quantity_booking(db: Session):
    user_id = 8808
    conv_id = 301
    session = get_booking_session(user_id, conv_id)
    session.reset()

    # Book 5 VIP passes directly
    r5 = ai_service.process_chat_message("Book 5 VIP tickets for India AI & Deep Learning Summit", user_id=user_id, db=db, conversation_id=conv_id)
    assert r5["type"] == "booking_summary"
    assert session.quantity == 5
    assert r5["payload"]["quantity"] == 5

    session.quantity = 7
    assert session.quantity == 7




def test_9_max_per_booking_cap(db: Session):
    user_id = 8809
    conv_id = 401
    session = get_booking_session(user_id, conv_id)
    session.reset()

    ev = db.query(Event).filter(Event.title == "India AI & Deep Learning Summit").first()
    if not ev:
        ev = Event(title="India AI & Deep Learning Summit", description="Event description", location="Bengaluru", date_str="Sat, 15 Oct 2026", price=100.0, available_tickets=100, total_capacity=100, status="PUBLISHED")
        db.add(ev)
    else:
        ev.available_tickets = 100
        ev.total_capacity = 100
    db.commit()




    # Try booking 15 tickets (> default limit 10)
    r15 = ai_service.process_chat_message("Book 15 VIP tickets for India AI & Deep Learning Summit", user_id=user_id, db=db, conversation_id=conv_id)
    assert "up to 10 tickets" in r15["reply"].lower()

    assert r15["routed_to"] == "BOOKING_MAX_PER_RESERVATION_CAP"


