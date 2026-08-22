import pytest
import uuid
from datetime import datetime, timedelta
from app.core.database import SessionLocal, engine, Base
from app.models.user import User
from app.models.ticket import Event, Ticket
from app.models.promo import PromoCode
from app.models.refund import RefundRequest
from app.services.seating_service import get_event_seat_map, hold_seats_atomic
from app.services.promo_service import validate_and_apply_promo
from app.services.refund_service import calculate_refund_amount, approve_refund
from app.services.transfer_service import initiate_ticket_transfer, accept_ticket_transfer
from app.api.v1.gates_api import list_event_gates
from app.api.v1.payouts_api import get_event_payout_ledger
from app.core.security import get_password_hash

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Seed test users
    user_customer = User(email="customer@test.com", name="Test Customer", hashed_password=get_password_hash("pass"), role="customer")
    user_org = User(email="org@test.com", name="Test Organizer", hashed_password=get_password_hash("pass"), role="organizer")
    user_admin = User(email="admin@test.com", name="Super Admin", hashed_password=get_password_hash("pass"), role="super_admin")
    db.add_all([user_customer, user_org, user_admin])
    db.commit()

    # Seed test event
    event = Event(
        id=1,
        title="AI Conclave 2026",
        description="Test event",
        category="Tech",
        location="Bengaluru",
        date_str="Fri, 20 Nov 2026",
        event_datetime=datetime.utcnow() + timedelta(days=10),
        price=500.0,
        total_capacity=100,
        available_tickets=100,
        organizer_id=user_org.id,
        status="PUBLISHED"
    )

    db.add(event)

    # Seed test promo
    promo = PromoCode(
        code="SAVE20",
        discount_type="PERCENTAGE",
        discount_value=20.0,
        max_uses=10,
        min_order_amount=200.0
    )
    db.add(promo)
    db.commit()
    db.close()

def test_seat_map_and_hold():
    db = SessionLocal()
    # 1. Fetch seat map
    seat_map = get_event_seat_map(db, 1)
    assert "VIP" in seat_map or "Standard" in seat_map

    # 2. Hold seats
    held = hold_seats_atomic(db, 1, 1, ["A-1", "A-2"])
    assert len(held) == 2
    assert held[0].status == "HELD"
    assert held[0].held_by_user_id == 1
    db.close()

def test_promo_and_refund_workflow():
    db = SessionLocal()

    # 1. Validate & Apply Promo
    res = validate_and_apply_promo(db, "SAVE20", 1, 1, 500.0)
    assert res["discount_amount"] == 100.0
    assert res["final_total"] == 400.0

    # 2. Create ticket
    ticket = Ticket(ticket_number="TKT-REF-001", event_id=1, user_id=1, status="CONFIRMED", price_paid=400.0)
    db.add(ticket)
    db.commit()

    # 3. Calculate refund amount
    event = db.query(Event).filter(Event.id == 1).first()
    eligible, note = calculate_refund_amount(db, ticket, event)
    assert eligible > 0.0

    refund_req = RefundRequest(ticket_id=ticket.id, user_id=1, event_id=1, amount_requested=400.0, amount_approved=eligible, status="REQUESTED")
    db.add(refund_req)
    db.commit()

    # 4. Approve refund
    approve_refund(db, refund_req, 2)
    assert refund_req.status == "REFUNDED"
    assert ticket.status == "REFUNDED"
    db.close()

def test_ticket_transfer_flow():
    db = SessionLocal()
    tkt = Ticket(ticket_number="TKT-TRF-001", event_id=1, user_id=1, status="CONFIRMED", price_paid=500.0)
    db.add(tkt)
    db.commit()

    # Initiate transfer to admin (user_id 3)
    transfer = initiate_ticket_transfer(db, tkt.id, 1, "admin@test.com")
    assert transfer.status in ["PENDING", "ACCEPTED"]

    # Verify old ticket invalidated
    db.refresh(tkt)
    assert tkt.status == "TRANSFERRED"
    db.close()

def test_multi_gate_and_payout_ledger():
    db = SessionLocal()
    user_org = db.query(User).filter(User.email == "org@test.com").first()

    # 1. Fetch gates
    gates = list_event_gates(1, db)
    assert len(gates) >= 2

    # 2. Fetch Payout Ledger
    ledger = get_event_payout_ledger(1, user_org, db)
    assert "gross_sales" in ledger
    assert "organizer_net" in ledger
    db.close()
