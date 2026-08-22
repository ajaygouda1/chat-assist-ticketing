import pytest
from datetime import datetime
from fastapi import HTTPException

from app.core.database import SessionLocal, engine, Base
from app.models.user import User
from app.models.ticket import Event, Ticket
from app.models.ticket_tier import TicketTier
from app.models.refund import RefundRequest
from app.models.seating import Seat
from app.services.tier_inventory_service import (
    create_or_update_event_tiers,
    hold_tier_inventory,
    confirm_tier_inventory_payment
)
from app.services.refund_service import approve_refund
from app.services.seating_service import initialize_event_seats
from app.core.security import get_password_hash

@pytest.fixture(autouse=True)
def setup_refund_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    user1 = User(id=1, email="cust1@test.com", name="Customer One", hashed_password=get_password_hash("pass"), role="customer")
    org = User(id=2, email="org@test.com", name="Org User", hashed_password=get_password_hash("pass"), role="organizer")
    db.add_all([user1, org])
    db.commit()

    event = Event(
        id=20,
        title="Refund Test Summit 2026",
        description="Event Desc",
        category="Tech",
        location="Bengaluru",
        date_str="Fri, 20 Nov 2026",
        price=1000.0,
        total_capacity=50,
        available_tickets=50,
        organizer_id=org.id,
        status="PUBLISHED"
    )
    db.add(event)
    db.commit()
    db.close()

def test_1_vip_x4_full_refund():
    """1. VIP x 4 full refund: sold 4->0, available 46->50, TOTAL=50 preserved"""
    db = SessionLocal()
    event = db.query(Event).filter(Event.id == 20).first()
    create_or_update_event_tiers(db, event, [{"name": "VIP Pass", "price": 1000.0, "total_quantity": 50, "max_per_order": 50}])

    # Customer buys 4 VIP tickets
    hold_tier_inventory(db, 20, "VIP Pass", 4, user_id=1)
    confirm_tier_inventory_payment(db, 20, "VIP Pass", 4)

    tier = db.query(TicketTier).filter(TicketTier.event_id == 20, TicketTier.name == "VIP Pass").first()
    assert tier.sold_quantity == 4
    assert tier.available_quantity == 46
    assert tier.total_quantity == tier.available_quantity + tier.held_quantity + tier.sold_quantity

    ticket = Ticket(id=101, ticket_number="TCK-VIP-4", event_id=20, user_id=1, status="CONFIRMED", price_paid=4000.0)
    db.add(ticket)
    db.commit()

    # Full refund request for all 4 tickets
    refund_req = RefundRequest(id=1, ticket_id=101, user_id=1, event_id=20, quantity_refunded=4, amount_requested=4000.0, amount_approved=4000.0, status="REQUESTED")
    db.add(refund_req)
    db.commit()

    approve_refund(db, refund_req, reviewer_id=2)

    db.refresh(tier)
    assert tier.sold_quantity == 0
    assert tier.available_quantity == 50
    assert tier.held_quantity == 0
    assert tier.total_quantity == tier.available_quantity + tier.held_quantity + tier.sold_quantity
    db.close()

def test_2_vip_x4_partial_refund_of_2():
    """2. VIP x 4 partial refund of 2: sold 4->2, available 46->48, TOTAL=50 preserved"""
    db = SessionLocal()
    event = db.query(Event).filter(Event.id == 20).first()
    create_or_update_event_tiers(db, event, [{"name": "VIP Pass", "price": 1000.0, "total_quantity": 50, "max_per_order": 50}])

    # Customer buys 4 VIP tickets
    hold_tier_inventory(db, 20, "VIP Pass", 4, user_id=1)
    confirm_tier_inventory_payment(db, 20, "VIP Pass", 4)

    tier = db.query(TicketTier).filter(TicketTier.event_id == 20, TicketTier.name == "VIP Pass").first()
    assert tier.sold_quantity == 4
    assert tier.available_quantity == 46

    ticket = Ticket(id=102, ticket_number="TCK-VIP-PARTIAL", event_id=20, user_id=1, status="CONFIRMED", price_paid=4000.0)
    db.add(ticket)
    db.commit()

    # Partial refund of 2 tickets
    refund_req = RefundRequest(id=2, ticket_id=102, user_id=1, event_id=20, quantity_refunded=2, amount_requested=2000.0, amount_approved=2000.0, status="REQUESTED")
    db.add(refund_req)
    db.commit()

    approve_refund(db, refund_req, reviewer_id=2)

    db.refresh(tier)
    assert tier.sold_quantity == 2
    assert tier.available_quantity == 48
    assert tier.held_quantity == 0
    assert tier.total_quantity == tier.available_quantity + tier.held_quantity + tier.sold_quantity
    db.close()

def test_3_idempotent_duplicate_refund_processing():
    """3. Calling approve_refund 5 times restores inventory EXACTLY ONCE"""
    db = SessionLocal()
    event = db.query(Event).filter(Event.id == 20).first()
    create_or_update_event_tiers(db, event, [{"name": "VIP Pass", "price": 1000.0, "total_quantity": 50, "max_per_order": 50}])

    hold_tier_inventory(db, 20, "VIP Pass", 2, user_id=1)
    confirm_tier_inventory_payment(db, 20, "VIP Pass", 2)

    tier = db.query(TicketTier).filter(TicketTier.event_id == 20, TicketTier.name == "VIP Pass").first()
    assert tier.sold_quantity == 2
    assert tier.available_quantity == 48

    ticket = Ticket(id=103, ticket_number="TCK-IDEM", event_id=20, user_id=1, status="CONFIRMED", price_paid=2000.0)
    db.add(ticket)
    db.commit()

    refund_req = RefundRequest(id=3, ticket_id=103, user_id=1, event_id=20, quantity_refunded=2, amount_requested=2000.0, amount_approved=2000.0, status="REQUESTED")
    db.add(refund_req)
    db.commit()

    # Call approve_refund 5 times concurrently or sequentially
    for _ in range(5):
        approve_refund(db, refund_req, reviewer_id=2)

    db.refresh(tier)
    # Must restore exactly 2 tickets, not 10!
    assert tier.sold_quantity == 0
    assert tier.available_quantity == 50
    assert tier.total_quantity == tier.available_quantity + tier.held_quantity + tier.sold_quantity
    db.close()

def test_4_transferred_ticket_refund_rejection():
    """4. Transferred ticket refund attempt is rejected with HTTP 400"""
    db = SessionLocal()
    ticket = Ticket(id=104, ticket_number="TCK-TRANSFERRED", event_id=20, user_id=1, status="TRANSFERRED", price_paid=1000.0)
    db.add(ticket)
    db.commit()

    from app.api.v1.refunds_api import request_refund
    from app.schemas.schemas import RefundCreateRequest

    req = RefundCreateRequest(ticket_id=104, quantity_refunded=1, reason="Refund transferred ticket")
    cust = db.query(User).filter(User.id == 1).first()

    with pytest.raises(HTTPException) as exc:
        request_refund(req, current_user=cust, db=db)

    assert "Cannot request refund for ticket with status 'TRANSFERRED'" in str(exc.value.detail)
    db.close()

def test_5_reserved_seat_refund_and_rebooking():
    """5. Reserved seat refund releases exact physical seat records for immediate rebooking"""
    db = SessionLocal()
    event = Event(id=21, title="Reserved Refund Summit", description="Desc", location="Blr", date_str="Fri, 20 Nov 2026", price=500.0, total_capacity=50, available_tickets=50, status="PUBLISHED")
    db.add(event)
    db.commit()

    initialize_event_seats(db, 21)
    seat = db.query(Seat).filter(Seat.event_id == 21, Seat.seat_code == "A-1").first()

    ticket = Ticket(id=105, ticket_number="TCK-SEAT-REFUND", event_id=21, user_id=1, status="CONFIRMED", price_paid=500.0)
    db.add(ticket)
    db.commit()

    # Assign seat to ticket
    seat.status = "SOLD"
    seat.ticket_id = ticket.id
    db.commit()

    # Process refund
    refund_req = RefundRequest(id=5, ticket_id=105, user_id=1, event_id=21, quantity_refunded=1, amount_requested=500.0, amount_approved=500.0, status="REQUESTED")
    db.add(refund_req)
    db.commit()

    approve_refund(db, refund_req, reviewer_id=2)

    db.refresh(seat)
    assert seat.status == "AVAILABLE"
    assert seat.ticket_id is None
    db.close()
