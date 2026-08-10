import sys
import os
import uuid
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from app.core.database import SessionLocal
from app.models.ticket import Event, Ticket
from app.services.qr_service import sign_ticket_token, verify_ticket_token, generate_ticket_qr_base64, get_qr_secret
from app.services.openai_service import ai_service
from app.ml.intent_router import intent_router
from app.api.v1.tickets import verify_ticket, check_in_ticket
from app.schemas.schemas import VerifyRequest, CheckInRequest

def test_qr_and_routing_fixes():
    db = SessionLocal()
    user_id = 888

    print("\n--- 1. TESTING QR GENERATION & HMAC TOKEN SECRET ---")
    secret = get_qr_secret()
    print(f"QR Signing Secret loaded: '{secret}'")
    assert secret is not None and len(secret) > 0

    token, qr_data_url = generate_ticket_qr_base64("10", "pay_test_10", "1")
    print(f"Generated Token: {token}")
    print(f"QR Data URL prefix: {qr_data_url[:30]}...")
    assert qr_data_url.startswith("data:image/")
    assert len(token.split(":")) == 5

    print("\n--- 2. TESTING QR VERIFICATION & WHITESPACE / TYPE NORMALIZATION ---")
    # Verify token with whitespace
    token_with_whitespace = f"  {token} \n"
    decoded = verify_ticket_token(token_with_whitespace)
    assert decoded is not None
    assert decoded["ticket_id"] == "10"
    assert decoded["event_id"] == "1"

    # Create dummy ticket in DB to test endpoint verify with string vs int event_id
    event = db.query(Event).first()
    if not event:
        event = Event(title="Test Event", price=100.0, available_tickets=10, total_capacity=10, status="PUBLISHED")
        db.add(event)
        db.commit()
        db.refresh(event)

    test_ticket = Ticket(
        ticket_number=f"TCK-{uuid.uuid4().hex[:6].upper()}",
        event_id=event.id,
        user_id=user_id,
        status="CONFIRMED",
        price_paid=100.0
    )
    db.add(test_ticket)
    db.commit()
    db.refresh(test_ticket)

    # Test verify_ticket with string event_id (e.g. event_id="1") vs integer event.id (1)
    req_verify = VerifyRequest(
        ticket_number=test_ticket.ticket_number,
        event_id=str(event.id)  # Pass string to verify int vs str normalization
    )
    res_verify = verify_ticket(req=req_verify, db=db)
    print(f"Verification Result (string event_id '{event.id}'):", res_verify.get("valid"), res_verify.get("message"))
    assert res_verify["valid"] is True
    assert res_verify["status"] == "CONFIRMED"

    # Test verify_ticket with No Scope Filter (event_id=None / "All Events")
    req_no_scope = VerifyRequest(
        ticket_number=test_ticket.ticket_number,
        event_id=None
    )
    res_no_scope = verify_ticket(req=req_no_scope, db=db)
    print("Verification Result (No Scope Filter / All Events):", res_no_scope.get("valid"), res_no_scope.get("message"))
    assert res_no_scope["valid"] is True


    # Test check-in endpoint
    req_checkin = CheckInRequest(ticket_id=test_ticket.id, staff_id="#GATE-1")
    res_checkin = check_in_ticket(req=req_checkin, db=db)
    print("Check-In Result:", res_checkin.get("status"), res_checkin.get("message"))
    assert res_checkin["success"] is True
    assert res_checkin["status"] == "CHECKED_IN"

    # Test re-verifying checked-in ticket (ALREADY_USED status handling)
    res_reverify = verify_ticket(req=req_verify, db=db)
    print("Re-verification of checked-in ticket:", res_reverify.get("status"))
    assert res_reverify["status"] == "ALREADY_USED"

    print("\n--- 3. TESTING INTENT ROUTER & CHAT ROUTING FALLBACKS ---")
    # Test intent router classification on diverse paraphrases
    res_search = intent_router.route_intent("are there any tech conferences this weekend?")
    print("Search query route:", res_search)
    assert res_search["intent"] == "search_event"

    res_general = ai_service.process_chat_message("what is your customer support hours?", user_id=user_id, db=db)
    print("General chat reply:", res_general.get("reply")[:60])
    assert res_general["intent"] == "general_chat"

    # Test state machine breakout when user asks search_event while in booking state
    ai_service.process_chat_message("Book ticket for Test Event", user_id=user_id, db=db)
    breakout_res = ai_service.process_chat_message("show my tickets", user_id=user_id, db=db)
    print("Breakout intent:", breakout_res.get("intent"))
    assert breakout_res["intent"] == "view_tickets"

    print("\n✅ ALL QR GENERATION, VERIFICATION, AND CHAT ROUTING FIXES VERIFIED SUCCESSFULLY!")

if __name__ == "__main__":
    test_qr_and_routing_fixes()
