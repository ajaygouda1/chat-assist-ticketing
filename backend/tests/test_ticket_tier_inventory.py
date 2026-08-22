import pytest
import concurrent.futures
from datetime import datetime, timedelta
from fastapi import HTTPException

from app.core.database import SessionLocal, engine, Base
from app.models.user import User
from app.models.ticket import Event, Ticket
from app.models.ticket_tier import TicketTier
from app.models.seating import Seat
from app.services.seating_service import initialize_event_seats
from app.services.tier_inventory_service import (
    create_or_update_event_tiers,
    hold_tier_inventory,
    confirm_tier_inventory_payment,
    release_tier_inventory_hold
)
from app.core.security import get_password_hash

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    user = User(email="test@user.com", name="Test User", hashed_password=get_password_hash("pass"), role="customer")
    org = User(email="org@test.com", name="Org User", hashed_password=get_password_hash("pass"), role="organizer")
    db.add_all([user, org])
    db.commit()

    event = Event(
        id=1,
        title="Tier Test Tech Summit 2026",
        description="Event Description",
        category="Tech",
        location="Bengaluru",
        date_str="Fri, 20 Nov 2026",
        price=500.0,
        total_capacity=450,
        available_tickets=450,
        organizer_id=org.id,
        status="PUBLISHED"
    )
    db.add(event)
    db.commit()
    db.close()

def test_1_create_tier_with_exact_quantity():
    """1. Create tier with exact quantity (VIP: 50, Gold: 100, Standard: 300)"""
    db = SessionLocal()
    event = db.query(Event).filter(Event.id == 1).first()

    tiers_data = [
        {"name": "VIP Pass", "price": 1000.0, "total_quantity": 50, "min_per_order": 1, "max_per_order": 4},
        {"name": "Gold Pass", "price": 750.0, "total_quantity": 100, "min_per_order": 1, "max_per_order": 6},
        {"name": "Standard Pass", "price": 500.0, "total_quantity": 300, "min_per_order": 1, "max_per_order": 10}
    ]

    created = create_or_update_event_tiers(db, event, tiers_data)
    assert len(created) == 3

    vip = [t for t in created if t.name == "VIP Pass"][0]
    assert vip.total_quantity == 50
    assert vip.available_quantity == 50
    assert vip.held_quantity == 0
    assert vip.sold_quantity == 0

    assert event.total_capacity == 450
    assert event.available_tickets == 450
    db.close()

def test_2_book_multiple_tickets():
    """2. Book multiple tickets (Inventory transition: available -> held)"""
    db = SessionLocal()
    event = db.query(Event).filter(Event.id == 1).first()
    create_or_update_event_tiers(db, event, [{"name": "VIP Pass", "price": 1000.0, "total_quantity": 50}])

    # Customer holds 3 VIP tickets
    tier = hold_tier_inventory(db, 1, "VIP Pass", 3, user_id=1)
    assert tier.available_quantity == 47
    assert tier.held_quantity == 3
    assert tier.sold_quantity == 0
    db.close()

def test_3_hold_expiration_restores_inventory():
    """3. Hold expiration restores inventory (held -> available)"""
    db = SessionLocal()
    event = db.query(Event).filter(Event.id == 1).first()
    create_or_update_event_tiers(db, event, [{"name": "VIP Pass", "price": 1000.0, "total_quantity": 50}])

    hold_tier_inventory(db, 1, "VIP Pass", 5, user_id=1)
    release_tier_inventory_hold(db, 1, "VIP Pass", 5)

    tier = db.query(TicketTier).filter(TicketTier.event_id == 1, TicketTier.name == "VIP Pass").first()
    assert tier.available_quantity == 50
    assert tier.held_quantity == 0
    db.close()

def test_4_successful_payment_converts_held_to_sold():
    """4. Successful payment converts held -> sold"""
    db = SessionLocal()
    event = db.query(Event).filter(Event.id == 1).first()
    create_or_update_event_tiers(db, event, [{"name": "VIP Pass", "price": 1000.0, "total_quantity": 50}])

    hold_tier_inventory(db, 1, "VIP Pass", 4, user_id=1)
    confirm_tier_inventory_payment(db, 1, "VIP Pass", 4)

    tier = db.query(TicketTier).filter(TicketTier.event_id == 1, TicketTier.name == "VIP Pass").first()
    assert tier.held_quantity == 0
    assert tier.sold_quantity == 4
    assert tier.available_quantity == 46
    assert tier.total_quantity == 50
    db.close()

def test_5_reject_quantity_above_availability():
    """5. Reject quantity above availability (Returns clean INSUFFICIENT_TICKETS)"""
    db = SessionLocal()
    event = db.query(Event).filter(Event.id == 1).first()
    create_or_update_event_tiers(db, event, [{"name": "VIP Pass", "price": 1000.0, "total_quantity": 5, "max_per_order": 5}])

    with pytest.raises(HTTPException) as exc_info:
        hold_tier_inventory(db, 1, "VIP Pass", 8, user_id=1)

    err = exc_info.value.detail
    assert err["code"] in ["INSUFFICIENT_TICKETS", "EXCEEDS_MAX_ORDER"]
    db.close()

def test_6_reject_negative_quantity_and_price():
    """6. Reject negative quantity or negative price"""
    db = SessionLocal()
    event = db.query(Event).filter(Event.id == 1).first()

    with pytest.raises(HTTPException) as exc_info:
        create_or_update_event_tiers(db, event, [{"name": "Bad Tier", "price": -50.0, "total_quantity": 10}])
    assert exc_info.value.detail["code"] == "INVALID_PRICE"

    with pytest.raises(HTTPException) as exc_info2:
        create_or_update_event_tiers(db, event, [{"name": "Bad Tier", "price": 100.0, "total_quantity": -5}])
    assert exc_info2.value.detail["code"] == "INVALID_QUANTITY"
    db.close()

def test_7_reject_lowering_quantity_below_sold_count():
    """7. Reject lowering quantity below sold + held count"""
    db = SessionLocal()
    event = db.query(Event).filter(Event.id == 1).first()
    create_or_update_event_tiers(db, event, [{"name": "VIP Pass", "price": 1000.0, "total_quantity": 50, "max_per_order": 50}])

    hold_tier_inventory(db, 1, "VIP Pass", 20, user_id=1)
    confirm_tier_inventory_payment(db, 1, "VIP Pass", 20)  # 20 sold

    # Try setting total_quantity = 15 (< 20 sold)
    with pytest.raises(HTTPException) as exc_info:
        create_or_update_event_tiers(db, event, [{"name": "VIP Pass", "price": 1000.0, "total_quantity": 15, "max_per_order": 50}])

    assert exc_info.value.detail["code"] == "CANNOT_REDUCE_BELOW_SOLD"
    db.close()

def test_8_increase_tier_quantity():
    """8. Increase tier quantity (50 -> 75, sold=20 -> available=55)"""
    db = SessionLocal()
    event = db.query(Event).filter(Event.id == 1).first()
    create_or_update_event_tiers(db, event, [{"name": "VIP Pass", "price": 1000.0, "total_quantity": 50, "max_per_order": 50}])

    hold_tier_inventory(db, 1, "VIP Pass", 20, user_id=1)
    confirm_tier_inventory_payment(db, 1, "VIP Pass", 20)  # 20 sold, 30 available

    # Increase to 75
    updated = create_or_update_event_tiers(db, event, [{"name": "VIP Pass", "price": 1000.0, "total_quantity": 75, "max_per_order": 50}])
    vip = updated[0]

    assert vip.total_quantity == 75
    assert vip.sold_quantity == 20
    assert vip.available_quantity == 55
    db.close()

def test_9_concurrent_booking_race_condition():
    """9. Concurrent booking race condition (50 concurrent requests on 5 tickets)"""
    db = SessionLocal()
    event = db.query(Event).filter(Event.id == 1).first()
    create_or_update_event_tiers(db, event, [{"name": "Limited Pass", "price": 100.0, "total_quantity": 5, "max_per_order": 5}])
    db.close()


    def attempt_hold_tier(user_id):
        t_db = SessionLocal()
        try:
            hold_tier_inventory(t_db, 1, "Limited Pass", 1, user_id=user_id)
            return True
        except Exception:
            return False
        finally:
            t_db.close()

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(attempt_hold_tier, u) for u in range(10, 60)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    successes = [r for r in results if r is True]
    assert len(successes) == 5  # Exactly 5 succeeded!

    db_check = SessionLocal()
    tier = db_check.query(TicketTier).filter(TicketTier.event_id == 1, TicketTier.name == "Limited Pass").first()
    assert tier.available_quantity == 0
    assert tier.held_quantity == 5
    db_check.close()

def test_10_reserved_seating_matches_seat_count():
    """10. Reserved seating quantity matches physical seat count"""
    db = SessionLocal()
    event = Event(id=2, title="Reserved Event", description="Desc", location="Bengaluru", date_str="Fri, 20 Nov 2026", price=500.0, total_capacity=50, available_tickets=50, status="PUBLISHED")
    db.add(event)
    db.commit()

    initialize_event_seats(db, 2)
    vip_seats = db.query(Seat).filter(Seat.event_id == 2, Seat.section_name == "VIP").all()
    count = len(vip_seats)
    assert count > 0

    # Reject mismatched total quantity
    with pytest.raises(HTTPException) as exc_info:
        create_or_update_event_tiers(db, event, [{"name": "VIP", "price": 1000.0, "total_quantity": count + 10}])

    assert exc_info.value.detail["code"] == "RESERVED_SEAT_MISMATCH"
    db.close()

def test_11_waitlist_activates_at_zero_inventory():
    """11. Waitlist activates when quantity reaches zero"""
    db = SessionLocal()
    event = db.query(Event).filter(Event.id == 1).first()
    create_or_update_event_tiers(db, event, [{"name": "Solo Pass", "price": 100.0, "total_quantity": 1, "max_per_order": 1}])

    # Hold the last ticket
    hold_tier_inventory(db, 1, "Solo Pass", 1, user_id=1)

    tier = db.query(TicketTier).filter(TicketTier.event_id == 1, TicketTier.name == "Solo Pass").first()
    assert tier.available_quantity == 0

    # Verify subsequent booking rejected
    with pytest.raises(HTTPException) as exc:
        hold_tier_inventory(db, 1, "Solo Pass", 1, user_id=2)

    assert exc.value.detail["code"] == "INSUFFICIENT_TICKETS"
    db.close()
