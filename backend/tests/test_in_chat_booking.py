import sys
import os
import uuid
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from app.core.database import SessionLocal, engine, Base
from app.models.ticket import Event, Ticket
from app.models.payment import Payment
from app.services.booking_conversation import get_booking_session, handle_book_ticket_turn, BookingState
from app.services.payment_service import confirm_payment
from app.services.openai_service import ai_service

def test_in_chat_direct_booking_flow():
    db = SessionLocal()
    user_id = 999

    print("\n--- IN-CHAT DIRECT BOOKING & PAYMENT TEST ---")

    # Step 1: Ensure demo event exists
    event = db.query(Event).filter(Event.available_tickets > 0).first()
    if not event:
        event = Event(
            title="AI Innovation Summit 2026",
            description="Leading AI Conference",
            category="Tech",
            location="Bengaluru",
            date_str="2026-09-15",
            price=499.0,
            total_capacity=10,
            available_tickets=10,
            status="PUBLISHED"
        )
        db.add(event)
        db.commit()
        db.refresh(event)

    print(f"1. Target Event: '{event.title}' (Price: INR {event.price}, Available: {event.available_tickets})")

    # Step 2: Turn 1 - User initiates booking
    session = get_booking_session(user_id)
    session.reset()
    assert session.state == BookingState.IDLE

    turn1 = ai_service.process_chat_message(f"Book ticket for {event.title}", user_id=user_id, db=db)
    print("Turn 1 Response Type:", turn1.get("type"))
    print("Turn 1 Reply:", turn1.get("reply"))
    assert turn1["type"] == "event_card"
    assert session.state == BookingState.EVENT_SELECTED

    # Step 3: Turn 2 - User specifies quantity & tier ("2 VIP Pass")
    turn2 = ai_service.process_chat_message("2 VIP Pass tickets", user_id=user_id, db=db)
    print("\nTurn 2 Response Type:", turn2.get("type"))
    print("Turn 2 Reply:", turn2.get("reply"))
    print("Turn 2 Summary Payload:", turn2.get("payload"))
    assert turn2["type"] == "booking_summary"
    assert session.state == BookingState.QTY_SELECTED
    assert turn2["payload"]["quantity"] == 2

    # Step 4: Turn 3 - User confirms booking ("Confirm booking")
    turn3 = ai_service.process_chat_message("Confirm booking", user_id=user_id, db=db)
    print("\nTurn 3 Response Type:", turn3.get("type"))
    print("Turn 3 Reply:", turn3.get("reply"))
    print("Turn 3 Payment Payload:", turn3.get("payload"))
    assert turn3["type"] == "payment_button"
    assert session.state == BookingState.PAYMENT_PENDING
    order_id = turn3["payload"]["order_id"]
    booking_id = turn3["payload"]["booking_id"]

    # Step 5: Verification & Payment Confirmation (§49e)
    pay_id = f"pay_test_inchat_{uuid.uuid4().hex[:6]}"
    confirm_res = confirm_payment(
        order_id=order_id,
        payment_id=pay_id,
        signature="mock_sig_ok",
        source="verify_api",
        booking_id=booking_id,
        user_id=user_id,
        db=db
    )
    print("\nPayment Confirmation Result:", confirm_res["status"])
    print("Ticket Details:", confirm_res.get("ticket"))
    assert confirm_res["status"] == "CONFIRMED"
    assert session.state == BookingState.PAID
    assert confirm_res["ticket"]["status"] == "CONFIRMED"
    assert confirm_res["ticket"]["qr_code_url"] is not None

    # Step 6: Test Idempotency (calling confirm_payment again with same order_id)
    idempotent_res = confirm_payment(
        order_id=order_id,
        payment_id=pay_id,
        signature="mock_sig_ok",
        source="webhook",
        user_id=user_id,
        db=db
    )
    print("\nIdempotency Check Result:", idempotent_res["status"])
    assert idempotent_res["status"] == "ALREADY_CONFIRMED"

    print("\n✅ ALL IN-CHAT BOOKING & PAYMENT TESTS PASSED PERFECTLY!")

if __name__ == "__main__":
    test_in_chat_direct_booking_flow()
