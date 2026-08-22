import pytest
import uuid
import concurrent.futures
from datetime import datetime, timedelta

from app.core.database import SessionLocal, engine, Base
from app.models.user import User, OrganizerProfile
from app.models.ticket import Event, Ticket
from app.models.seating import Seat
from app.services.seating_service import initialize_event_seats, hold_seats_atomic
from app.models.promo import PromoCode
from app.models.refund import RefundRequest
from app.services.event_lifecycle import transition_event_status
from app.services.booking_fsm import transition_booking_status, BookingDraft
from app.services.promo_service import validate_and_apply_promo
from app.services.payment_service import confirm_payment
from app.services.refund_service import calculate_refund_amount, approve_refund
from app.services.transfer_service import initiate_ticket_transfer, accept_ticket_transfer
from app.api.v1.tickets import verify_ticket, check_in_ticket
from app.schemas.schemas import VerifyRequest, CheckInRequest
from app.core.security import get_password_hash

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Seed Admin & Users
    admin = User(email="admin@test.com", name="Admin", hashed_password=get_password_hash("pass"), role="super_admin")
    cust1 = User(email="cust1@test.com", name="Customer 1", hashed_password=get_password_hash("pass"), role="customer")
    cust2 = User(email="cust2@test.com", name="Customer 2", hashed_password=get_password_hash("pass"), role="customer")
    db.add_all([admin, cust1, cust2])
    db.commit()
    db.close()

def test_scenario_a_organizer_workflow():
    """Scenario A: Register -> Become Organizer -> Create Event -> Create Seat Map -> Publish"""
    db = SessionLocal()
    org_user = User(email="org_a@test.com", name="Org A", hashed_password=get_password_hash("pass"), role="organizer")
    db.add(org_user)
    db.commit()

    profile = OrganizerProfile(user_id=org_user.id, organization_name="Org A Corp", kyc_status="VERIFIED")
    db.add(profile)
    db.commit()

    event = Event(
        title="Tech Summit 2026",
        description="Official Tech Summit",
        category="Tech",
        location="Bengaluru Arena",
        date_str="Sat, 15 Oct 2026",
        price=500.0,
        total_capacity=100,
        available_tickets=100,
        organizer_id=org_user.id,
        status="DRAFT"
    )
    db.add(event)
    db.commit()

    # Create seat map
    initialize_event_seats(db, event.id)
    seats = db.query(Seat).filter(Seat.event_id == event.id).all()
    assert len(seats) > 0

    # Publish via Lifecycle FSM
    transition_event_status(event, "PUBLISHED")
    db.commit()
    assert event.status == "PUBLISHED"
    db.close()

def test_scenario_b_customer_booking_and_payment():
    """Scenario B: Discover -> Select Seat -> Apply Promo -> Create Hold -> Complete Payment -> Receive QR Ticket"""
    db = SessionLocal()
    event = Event(
        id=10,
        title="Music Fest",
        description="Music Fest",
        category="Music",
        location="Indiranagar",
        date_str="Sun, 20 Oct 2026",
        price=400.0,
        total_capacity=50,
        available_tickets=50,
        status="PUBLISHED"
    )
    promo = PromoCode(code="SAVE10", discount_type="PERCENTAGE", discount_value=10.0, max_uses=10, min_order_amount=100.0)
    db.add_all([event, promo])
    db.commit()

    initialize_event_seats(db, 10)

    # 1. Hold seat
    held = hold_seats_atomic(db, 10, 2, ["A-1"])
    assert len(held) == 1
    assert held[0].status == "HELD"

    # Set active booking session for user 2
    from app.services.booking_conversation import get_booking_session
    sess = get_booking_session(2)
    sess.event_id = 10
    sess.quantity = 1
    sess.unit_price = 400.0

    # 2. Apply promo
    promo_res = validate_and_apply_promo(db, "SAVE10", 2, 10, 400.0)
    assert promo_res["discount_amount"] == 40.0
    assert promo_res["final_total"] == 360.0

    # 3. Confirm Payment
    order_id = f"order_{uuid.uuid4().hex[:8]}"
    pay_res = confirm_payment(order_id=order_id, payment_id=f"pay_{uuid.uuid4().hex[:8]}", signature="trusted_sig", source="test", user_id=2, db=db)
    tkt_num = pay_res.get("ticket_number") or pay_res.get("ticket", {}).get("ticket_number")
    assert tkt_num and tkt_num.startswith("TCK-")

    db.close()

def test_scenario_c_gate_single_use_checkin():
    """Scenario C: Scan Valid QR -> CHECKED_IN, Scan Same QR Again -> ALREADY_USED"""
    db = SessionLocal()
    event = Event(id=20, title="Comedy Show", description="Desc", category="Comedy", location="HSR", date_str="Fri, 1 Nov 2026", price=200.0, available_tickets=20, status="PUBLISHED")
    db.add(event)
    db.commit()

    tkt = Ticket(ticket_number="TCK-GATE-100", event_id=20, user_id=2, status="CONFIRMED", price_paid=200.0)
    db.add(tkt)
    db.commit()

    # 1st Scan
    req1 = CheckInRequest(ticket_id=tkt.id, staff_id="#STAFF-A")
    res1 = check_in_ticket(req=req1, db=db)
    assert res1["success"] is True
    assert res1["status"] == "CHECKED_IN"

    # 2nd Scan (Duplicate Guard)
    req2 = VerifyRequest(ticket_number="TCK-GATE-100", event_id=20)
    res2 = verify_ticket(req=req2, db=db)
    assert res2["status"] == "ALREADY_USED"
    db.close()

def test_scenario_d_refund_and_invalidation():
    """Scenario D: Request Refund -> Approve -> Process Refund -> QR Invalidated -> Gate Scan Rejected"""
    db = SessionLocal()
    event = Event(id=30, title="Cyber Con", description="Desc", category="Tech", location="UB City", date_str="Dec 2026", event_datetime=datetime.utcnow() + timedelta(days=10), price=300.0, available_tickets=20, status="PUBLISHED")
    db.add(event)
    db.commit()

    tkt = Ticket(ticket_number="TCK-REF-300", event_id=30, user_id=2, status="CONFIRMED", price_paid=300.0)
    db.add(tkt)
    db.commit()

    # Refund request & approval
    eligible, note = calculate_refund_amount(db, tkt, event)
    req = RefundRequest(ticket_id=tkt.id, user_id=2, event_id=30, amount_requested=300.0, amount_approved=eligible, status="REQUESTED")
    db.add(req)
    db.commit()

    approve_refund(db, req, 1)
    assert tkt.status == "REFUNDED"

    # Verify Gate scan rejected
    res = verify_ticket(req=VerifyRequest(ticket_number="TCK-REF-300", event_id=30), db=db)
    assert res["valid"] is False
    assert res["status"] == "CANCELLED_OR_REFUNDED"
    db.close()

def test_scenario_e_ticket_transfer():
    """Scenario E: Transfer Ticket -> Recipient Accepts -> Original QR Invalidated -> Recipient QR Valid"""
    db = SessionLocal()
    tkt = Ticket(ticket_number="TCK-TRF-500", event_id=10, user_id=2, status="CONFIRMED", price_paid=400.0)
    db.add(tkt)
    db.commit()

    # Transfer to cust2 (user_id 3, email cust2@test.com)
    transfer = initiate_ticket_transfer(db, tkt.id, 2, "cust2@test.com")
    db.refresh(tkt)
    assert tkt.status == "TRANSFERRED"

    # Verify old ticket invalid at gate
    res_old = verify_ticket(req=VerifyRequest(ticket_number="TCK-TRF-500", event_id=10), db=db)
    assert res_old["valid"] is False

    # Verify new recipient ticket confirmed
    new_tkt = db.query(Ticket).filter(Ticket.user_id == 3, Ticket.status == "CONFIRMED").first()
    assert new_tkt is not None
    res_new = verify_ticket(req=VerifyRequest(ticket_number=new_tkt.ticket_number, event_id=10), db=db)
    assert res_new["valid"] is True
    db.close()

def test_scenario_f_concurrency_race():
    """Scenario F: 50 users attempt the same seat -> exactly one successful owner"""
    db = SessionLocal()
    event = Event(id=99, title="VIP Concert", description="Desc", category="Music", location="Bengaluru", date_str="Dec 2026", price=1000.0, available_tickets=10, status="PUBLISHED")
    db.add(event)
    db.commit()
    initialize_event_seats(db, 99)
    db.close()

    def attempt_hold(user_id):
        db_thread = SessionLocal()
        try:
            res = hold_seats_atomic(db_thread, 99, user_id, ["A-1"])
            return (user_id, True)
        except Exception:
            return (user_id, False)
        finally:
            db_thread.close()

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(attempt_hold, u) for u in range(10, 60)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    successes = [r for r in results if r[1] is True]
    assert len(successes) == 1  # Exactly one winner!
