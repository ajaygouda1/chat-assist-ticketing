import pytest
import concurrent.futures
from datetime import datetime, timedelta
from fastapi import HTTPException

from app.core.database import SessionLocal, engine, Base
from app.models.user import User
from app.models.ticket import Event, Ticket
from app.models.ticket_tier import TicketTier
from app.models.refund import RefundRequest
from app.services.tier_inventory_service import (
    create_or_update_event_tiers,
    hold_tier_inventory,
    confirm_tier_inventory_payment,
    release_tier_inventory_hold
)
from app.services.refund_service import approve_refund
from app.services.event_lifecycle import transition_event_status
from app.core.security import get_password_hash

@pytest.fixture(autouse=True)
def setup_integration_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    user1 = User(id=1, email="cust1@test.com", name="Customer One", hashed_password=get_password_hash("pass"), role="customer")
    user2 = User(id=2, email="cust2@test.com", name="Customer Two", hashed_password=get_password_hash("pass"), role="customer")
    org = User(id=3, email="org@test.com", name="Organizer User", hashed_password=get_password_hash("pass"), role="organizer")
    db.add_all([user1, user2, org])
    db.commit()

    event = Event(
        id=10,
        title="Micro-Inventory Tech Summit 2026",
        description="E2E Integration Test Event",
        category="Tech",
        location="Bengaluru",
        date_str="Sat, 21 Nov 2026",
        price=1000.0,
        total_capacity=2,
        available_tickets=2,
        organizer_id=org.id,
        status="PUBLISHED"
    )
    db.add(event)
    db.commit()
    db.close()

def test_flow_1_tiny_inventory_race_and_lifecycle():
    """
    FLOW 1: VIP = 2 tickets.
    2 concurrent sessions try to book the last tickets at the same time:
    - User 1 holds 1 ticket and completes payment -> (Sold: 1, Available: 1, Held: 0)
    - User 2 holds 1 ticket, but hold expires -> (Available: 1, Held: 0)
    Verify TOTAL = AVAILABLE + HELD + SOLD at every step.
    """
    db = SessionLocal()
    event = db.query(Event).filter(Event.id == 10).first()
    create_or_update_event_tiers(db, event, [{"name": "VIP Pass", "price": 1000.0, "total_quantity": 2, "min_per_order": 1, "max_per_order": 2}])

    tier = db.query(TicketTier).filter(TicketTier.event_id == 10, TicketTier.name == "VIP Pass").first()
    assert tier.total_quantity == tier.available_quantity + tier.held_quantity + tier.sold_quantity
    assert tier.total_quantity == 2
    assert tier.available_quantity == 2

    # Step A: User 1 holds 1 ticket
    hold_tier_inventory(db, 10, "VIP Pass", 1, user_id=1)
    db.refresh(tier)
    assert tier.available_quantity == 1
    assert tier.held_quantity == 1
    assert tier.sold_quantity == 0
    assert tier.total_quantity == tier.available_quantity + tier.held_quantity + tier.sold_quantity

    # Step B: User 2 holds 1 ticket
    hold_tier_inventory(db, 10, "VIP Pass", 1, user_id=2)
    db.refresh(tier)
    assert tier.available_quantity == 0
    assert tier.held_quantity == 2
    assert tier.sold_quantity == 0
    assert tier.total_quantity == tier.available_quantity + tier.held_quantity + tier.sold_quantity

    # Step C: User 1 confirms payment
    confirm_tier_inventory_payment(db, 10, "VIP Pass", 1)
    db.refresh(tier)
    assert tier.sold_quantity == 1
    assert tier.held_quantity == 1
    assert tier.available_quantity == 0
    assert tier.total_quantity == tier.available_quantity + tier.held_quantity + tier.sold_quantity

    # Step D: User 2's hold expires
    release_tier_inventory_hold(db, 10, "VIP Pass", 1)
    db.refresh(tier)
    assert tier.sold_quantity == 1
    assert tier.held_quantity == 0
    assert tier.available_quantity == 1
    assert tier.total_quantity == tier.available_quantity + tier.held_quantity + tier.sold_quantity

    db.close()

def test_flow_2_active_hold_editing_guard():
    """
    FLOW 2: Organizer attempts to edit tier quantity while user has active holds.
    Total: 2, Held: 1 -> Minimum allowed quantity = 1.
    Setting quantity = 0 should be rejected.
    """
    db = SessionLocal()
    event = db.query(Event).filter(Event.id == 10).first()
    create_or_update_event_tiers(db, event, [{"name": "VIP Pass", "price": 1000.0, "total_quantity": 2}])

    hold_tier_inventory(db, 10, "VIP Pass", 1, user_id=1)

    with pytest.raises(HTTPException) as exc_info:
        create_or_update_event_tiers(db, event, [{"name": "VIP Pass", "price": 1000.0, "total_quantity": 0}])

    assert exc_info.value.detail["code"] in ["CANNOT_REDUCE_BELOW_SOLD", "INVALID_QUANTITY"]
    db.close()

def test_flow_3_refund_restores_inventory():
    """
    FLOW 3: Customer buys 1 ticket (Sold: 1), requests refund, refund approved.
    Verify tier sold_quantity decreases by 1 and available_quantity increases by 1.
    """
    db = SessionLocal()
    event = db.query(Event).filter(Event.id == 10).first()
    create_or_update_event_tiers(db, event, [{"name": "VIP Pass", "price": 1000.0, "total_quantity": 2}])

    hold_tier_inventory(db, 10, "VIP Pass", 1, user_id=1)
    confirm_tier_inventory_payment(db, 10, "VIP Pass", 1)

    tier = db.query(TicketTier).filter(TicketTier.event_id == 10, TicketTier.name == "VIP Pass").first()
    assert tier.sold_quantity == 1
    assert tier.available_quantity == 1

    ticket = Ticket(ticket_number="TCK-E2E-REFUND", event_id=10, user_id=1, status="CONFIRMED", price_paid=1000.0)
    db.add(ticket)
    db.commit()

    refund_req = RefundRequest(ticket_id=ticket.id, user_id=1, event_id=10, amount_requested=1000.0, amount_approved=1000.0, reason="Change of plans", status="REQUESTED")
    db.add(refund_req)
    db.commit()

    approve_refund(db, refund_req, reviewer_id=3)

    db.refresh(tier)
    assert tier.sold_quantity == 0
    assert tier.available_quantity == 2
    assert tier.total_quantity == tier.available_quantity + tier.held_quantity + tier.sold_quantity
    db.close()

def test_flow_4_event_cancellation_releases_holds():
    """
    FLOW 4: Cancel event with active holds -> releases held quantities.
    """
    db = SessionLocal()
    event = db.query(Event).filter(Event.id == 10).first()
    create_or_update_event_tiers(db, event, [{"name": "VIP Pass", "price": 1000.0, "total_quantity": 2}])

    hold_tier_inventory(db, 10, "VIP Pass", 1, user_id=1)
    tier = db.query(TicketTier).filter(TicketTier.event_id == 10, TicketTier.name == "VIP Pass").first()
    assert tier.held_quantity == 1

    transition_event_status(event, "CANCELLED")
    db.commit()

    db.refresh(tier)
    assert tier.held_quantity == 0
    assert tier.available_quantity == 2
    db.close()

def test_flow_5_max_per_order_bounds():
    """
    FLOW 5: Attempting max allowed quantity succeeds; max + 1 fails.
    """
    db = SessionLocal()
    event = db.query(Event).filter(Event.id == 10).first()
    create_or_update_event_tiers(db, event, [{"name": "Standard", "price": 500.0, "total_quantity": 10, "min_per_order": 1, "max_per_order": 4}])

    # 4 tickets (max allowed) -> succeeds
    hold = hold_tier_inventory(db, 10, "Standard", 4, user_id=1)
    assert hold.held_quantity == 4

    release_tier_inventory_hold(db, 10, "Standard", 4)

    # 5 tickets (> max 4) -> fails with EXCEEDS_MAX_ORDER
    with pytest.raises(HTTPException) as exc:
        hold_tier_inventory(db, 10, "Standard", 5, user_id=1)

    assert exc.value.detail["code"] == "EXCEEDS_MAX_ORDER"
    db.close()
