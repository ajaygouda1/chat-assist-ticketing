import sys
import os
import uuid
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from fastapi import Request
from app.core.database import SessionLocal
from app.models.user import User
from app.models.ticket import Event, Ticket
from app.models.payment import Payment
from app.api.v1.tickets import get_ticket_wallet_links, transfer_ticket, expire_abandoned_booking, verify_ticket
from app.api.v1.social_preview import get_event_social_preview
from app.api.v1.organizer import draft_description, emergency_broadcast
from app.schemas.schemas import TransferRequest, DraftRequest, BroadcastRequest, VerifyRequest
from app.services.wallet_service import generate_google_wallet_link, generate_apple_wallet_link

def test_addendum_features():
    db = SessionLocal()

    print("\n--- 1. TESTING §57a WALLET PASSES ---")
    ev = Event(
        title="AI Tech Summit 2026",
        description="Exploring cutting-edge LLMs and agentic AI models.",
        location="Bengaluru International Centre",
        date_str="20 Oct 2026",
        price=1500.0,
        available_tickets=50,
        total_capacity=50,
        status="PUBLISHED"
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)

    user1 = User(email=f"owner_{uuid.uuid4().hex[:4]}@example.com", name="Original Owner", hashed_password="pass", role="customer")
    db.add(user1)
    db.commit()
    db.refresh(user1)

    from app.services.qr_service import generate_ticket_qr_base64
    initial_qr_token, _ = generate_ticket_qr_base64("101", "pay_init", str(ev.id))

    t1 = Ticket(
        ticket_number=f"TCK-WLT-{uuid.uuid4().hex[:6].upper()}",
        event_id=ev.id,
        user_id=user1.id,
        status="CONFIRMED",
        price_paid=1500.0,
        qr_code_path=initial_qr_token
    )
    db.add(t1)
    db.commit()
    db.refresh(t1)

    # Update initial QR token with actual t1.id
    initial_qr_token, _ = generate_ticket_qr_base64(str(t1.id), "pay_init", str(ev.id))
    t1.qr_code_path = initial_qr_token
    db.commit()


    wallet_res = get_ticket_wallet_links(ticket_id=t1.id, db=db)
    assert wallet_res["ticket_id"] == t1.id
    assert "https://pay.google.com/gp/v/save/" in wallet_res["google_wallet_url"]
    assert f"/api/tickets/{t1.id}/pass.pkpass" in wallet_res["apple_wallet_url"]
    print("✅ §57a Wallet passes verified:", wallet_res["google_wallet_url"][:60] + "...")

    print("\n--- 2. TESTING §57b ABANDONED BOOKING RECOVERY ---")
    pay_pending = Payment(
        payment_id=f"pay_abnd_{uuid.uuid4().hex[:6]}",
        order_id=f"ord_abnd_{uuid.uuid4().hex[:6]}",
        ticket_id=t1.id,
        user_id=user1.id,
        amount=1500.0,
        status="PAYMENT_PENDING",
        invoice_number=f"INV-ABND-{uuid.uuid4().hex[:4].upper()}"
    )
    db.add(pay_pending)
    db.commit()
    db.refresh(pay_pending)

    recovery_res = expire_abandoned_booking(booking_id=pay_pending.id, db=db)
    assert recovery_res["success"] is True
    assert recovery_res["status"] == "EXPIRED_RELEASED"
    assert recovery_res["recovery_notification"]["scheduled"] is True
    print("✅ §57b Abandoned booking recovery verified:", recovery_res["message"])

    print("\n--- 3. TESTING §57c SOCIAL SHARE PREVIEWS (OPEN GRAPH TAGS) ---")
    scope = {"type": "http", "method": "GET", "path": f"/events/{ev.id}", "headers": [(b"user-agent", b"WhatsApp/2.21.12")]}
    dummy_req = Request(scope)
    og_res = get_event_social_preview(event_id=ev.id, request=dummy_req, db=db)
    assert "og:title" in og_res.body.decode("utf-8")
    assert ev.title in og_res.body.decode("utf-8")
    print("✅ §57c Open Graph tags rendered successfully for social bots.")

    print("\n--- 4. TESTING §57d TICKET TRANSFER & TOKEN RE-SIGNING ---")
    recipient_email = f"friend_{uuid.uuid4().hex[:4]}@example.com"
    old_qr_token = t1.qr_code_path

    transfer_res = transfer_ticket(
        ticket_id=t1.id,
        payload=TransferRequest(recipient_email=recipient_email),
        current_user=user1,
        db=db
    )

    assert transfer_res["success"] is True
    db.refresh(t1)
    assert t1.qr_code_path != old_qr_token, "QR Token should be re-signed so old screenshot dies!"

    # Verify old token is rejected / fails verification
    verify_old = verify_ticket(req=VerifyRequest(qr_token=old_qr_token), db=db)
    assert verify_old["valid"] is False, "Old pre-transfer QR token must fail verification!"
    
    # Verify new token succeeds
    verify_new = verify_ticket(req=VerifyRequest(qr_token=t1.qr_code_path), db=db)
    assert verify_new["valid"] is True, "New post-transfer QR token must be valid!"
    print("✅ §57d Ticket transfer verified! Old QR token invalidated, new QR token validated.")

    print("\n--- 5. TESTING §57e AI EVENT DESCRIPTION DRAFTING ---")
    draft_res = draft_description(payload=DraftRequest(bullet_points="Web3 conference, keynotes by vitalik, hackathon with $50k prizes"), db=db)

    assert draft_res["success"] is True
    assert len(draft_res["draft"]) > 15
    print("✅ §57e AI Description drafting verified:", draft_res["draft"][:80] + "...")

    print("\n--- 6. TESTING §57f EMERGENCY BROADCAST TO CHECKED-IN ATTENDEES ---")
    # Mark ticket as CHECKED_IN
    t1.status = "CHECKED_IN"
    db.commit()

    broadcast_res = emergency_broadcast(
        event_id=ev.id,
        payload=BroadcastRequest(message="Severe weather warning: move indoors to Main Auditorium", priority="high"),
        current_user=user1,
        owner_check=ev,
        db=db
    )
    assert broadcast_res["success"] is True
    assert broadcast_res["broadcast"]["notified_count"] >= 1
    print("✅ §57f Emergency broadcast verified:", broadcast_res["message"])

    db.close()
