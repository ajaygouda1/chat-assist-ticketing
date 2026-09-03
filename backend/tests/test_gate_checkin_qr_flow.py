import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal
from app.models.ticket import Event, Ticket
from app.models.payment import Payment
from app.services.payment_service import confirm_payment
from app.services.qr_service import generate_ticket_qr_base64, verify_ticket_token, sign_ticket_token
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_payment_generates_valid_qr_token(db_session):
    """Verifies that confirming payment creates ticket records with non-empty cryptographic qr_token."""
    from app.models.booking_draft import BookingDraft
    from datetime import datetime, timedelta

    ev = db_session.query(Event).filter(Event.available_tickets > 2, Event.status == "PUBLISHED").first()
    assert ev is not None

    draft1 = BookingDraft(
        draft_number=f"DFT-{os.urandom(4).hex().upper()}",
        user_id=1,
        event_id=ev.id,
        ticket_type="Standard",
        quantity=1,
        unit_price=float(ev.price),
        subtotal=float(ev.price),
        tax=round(float(ev.price) * 0.18, 2),
        total=round(float(ev.price) * 1.18, 2),
        status="READY_FOR_PAYMENT",
        expires_at=datetime.utcnow() + timedelta(minutes=10)
    )
    db_session.add(draft1)
    db_session.commit()
    db_session.refresh(draft1)

    pay_res = confirm_payment(
        order_id=f"ord_qr_{os.urandom(4).hex()}",
        payment_id=f"pay_qr_{os.urandom(4).hex()}",
        signature="mock_sig_qr",
        source="test_gate_qr",
        booking_id=draft1.id,
        user_id=1,
        db=db_session
    )
    assert pay_res["status"] in ["CONFIRMED", "ALREADY_CONFIRMED"]
    ticket_data = pay_res["ticket"]
    assert ticket_data["ticket_number"].startswith("TCK-")
    assert ticket_data["qr_token"] is not None
    assert len(ticket_data["qr_token"]) > 20

    # Verify signature locally
    parsed_data = verify_ticket_token(ticket_data["qr_token"])
    assert parsed_data is not None
    assert str(parsed_data["ticket_id"]) == str(ticket_data["id"])
    assert str(parsed_data["event_id"]) == str(ev.id)


def test_gate_checkin_lifecycle_and_duplicate_scan(db_session):
    """
    Mandatory gate verification tests:
    1. Scan valid ticket QR -> CONFIRMED
    2. Check-in attendee -> CHECKED_IN
    3. Rescan same ticket QR -> ALREADY_USED
    4. Scan tampered fake QR -> INVALID
    5. Scan cancelled ticket -> CANCELLED
    """
    from app.models.booking_draft import BookingDraft
    from datetime import datetime, timedelta

    ev = db_session.query(Event).filter(Event.available_tickets > 2, Event.status == "PUBLISHED").first()

    draft2 = BookingDraft(
        draft_number=f"DFT-{os.urandom(4).hex().upper()}",
        user_id=1,
        event_id=ev.id,
        ticket_type="VIP Pass",
        quantity=1,
        unit_price=float(ev.price),
        subtotal=float(ev.price),
        tax=round(float(ev.price) * 0.18, 2),
        total=round(float(ev.price) * 1.18, 2),
        status="READY_FOR_PAYMENT",
        expires_at=datetime.utcnow() + timedelta(minutes=10)
    )
    db_session.add(draft2)
    db_session.commit()
    db_session.refresh(draft2)

    pay_res = confirm_payment(
        order_id=f"ord_gate_{os.urandom(4).hex()}",
        payment_id=f"pay_gate_{os.urandom(4).hex()}",
        signature="mock_sig_gate",
        source="test_gate_flow",
        booking_id=draft2.id,
        user_id=1,
        db=db_session
    )
    ticket_data = pay_res["ticket"]
    ticket_id = ticket_data["id"]
    qr_token = ticket_data["qr_token"]

    # Step 1: Optical / token verification before check-in
    res_verify = client.post("/api/v1/tickets/verify", json={
        "qr_token": qr_token,
        "event_id": str(ev.id)
    })
    assert res_verify.status_code == 200
    data_v1 = res_verify.json()
    assert data_v1["valid"] is True
    assert data_v1["status"] == "CONFIRMED"
    assert data_v1["ticket"]["id"] == ticket_id

    # Step 2: Perform gate check-in
    res_checkin = client.post(f"/api/v1/tickets/{ticket_id}/check-in", json={
        "ticket_id": ticket_id,
        "staff_id": "#GATE-STAFF-NORTH"
    })
    assert res_checkin.status_code == 200
    data_ci = res_checkin.json()
    assert data_ci["status"] == "CHECKED_IN"

    # Step 3: Second scan of the same QR token must return ALREADY_USED
    res_rescan = client.post("/api/v1/tickets/verify", json={
        "qr_token": qr_token,
        "event_id": str(ev.id)
    })
    assert res_rescan.status_code == 200
    data_v2 = res_rescan.json()
    assert data_v2["valid"] is False
    assert data_v2["status"] == "ALREADY_USED"
    assert "Already Checked In" in data_v2["message"]

    # Step 4: Scan tampered fake QR must return INVALID
    fake_token = qr_token[:-6] + "BADSIG"
    res_fake = client.post("/api/v1/tickets/verify", json={
        "qr_token": fake_token,
        "event_id": str(ev.id)
    })
    assert res_fake.status_code == 200
    data_fake = res_fake.json()
    assert data_fake["valid"] is False
    assert data_fake["status"] == "INVALID"

    # Step 5: Test cancelled ticket
    ticket = db_session.query(Ticket).filter(Ticket.id == ticket_id).first()
    ticket.status = "CANCELLED"
    db_session.commit()

    res_cancel_scan = client.post("/api/v1/tickets/verify", json={
        "qr_token": qr_token,
        "event_id": str(ev.id)
    })
    assert res_cancel_scan.status_code == 200
    data_cancel = res_cancel_scan.json()
    assert data_cancel["valid"] is False
    assert "CANCELLED" in data_cancel["status"]
