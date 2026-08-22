from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Dict, Any
from fastapi import HTTPException
from app.models.seating import Seat, Section, Venue
from app.models.ticket import Event

def initialize_event_seats(db: Session, event_id: int, total_capacity: int = 100):
    """
    Initializes a seat map for an event with sections: VIP (rows A-B), Gold (rows C-E), Standard (rows F-J).
    """
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        return
    
    # Check if seats already exist
    existing = db.query(Seat).filter(Seat.event_id == event_id).first()
    if existing:
        return

    sections_config = [
        {"name": "VIP", "tier": "VIP", "rows": ["A", "B"], "seats_per_row": 10, "price": round(event.price * 1.5, 2)},
        {"name": "Gold", "tier": "Gold", "rows": ["C", "D", "E"], "seats_per_row": 10, "price": round(event.price * 1.2, 2)},
        {"name": "Standard", "tier": "Standard", "rows": ["F", "G", "H", "I", "J"], "seats_per_row": 10, "price": round(event.price, 2)}
    ]

    for sec in sections_config:
        section_obj = Section(
            event_id=event_id,
            name=sec["name"],
            pricing_tier=sec["tier"],
            price_multiplier=1.5 if sec["tier"] == "VIP" else (1.2 if sec["tier"] == "Gold" else 1.0)
        )
        db.add(section_obj)
        db.flush()

        for row in sec["rows"]:
            for num in range(1, sec["seats_per_row"] + 1):
                seat_code = f"{row}-{num}"
                seat = Seat(
                    event_id=event_id,
                    section_id=section_obj.id,
                    section_name=sec["name"],
                    row_label=row,
                    seat_number=num,
                    seat_code=seat_code,
                    status="AVAILABLE",
                    price=sec["price"]
                )
                db.add(seat)
    db.commit()

def hold_seats_atomic(db: Session, event_id: int, user_id: int, seat_codes: List[str]) -> List[Seat]:
    """
    Atomically locks seats for 10 minutes. Cleans up expired holds first.
    Prevents race conditions / duplicate bookings of the same seat.
    """
    now = datetime.utcnow()
    
    # Release any expired holds for this event
    expired_seats = db.query(Seat).filter(
        Seat.event_id == event_id,
        Seat.status == "HELD",
        Seat.held_until < now
    ).all()
    for s in expired_seats:
        s.status = "AVAILABLE"
        s.held_by_user_id = None
        s.held_until = None
    db.commit()

    # Query requested seats
    target_seats = db.query(Seat).filter(
        Seat.event_id == event_id,
        Seat.seat_code.in_(seat_codes)
    ).with_for_update().all()

    if len(target_seats) != len(seat_codes):
        raise HTTPException(status_code=400, detail="Some selected seats do not exist")

    from app.core.redis import redis_manager

    for s in target_seats:
        if s.status == "SOLD":
            raise HTTPException(status_code=400, detail=f"Seat {s.seat_code} is already sold")
        if s.status == "HELD" and s.held_by_user_id != user_id and s.held_until and s.held_until > now:
            raise HTTPException(status_code=400, detail=f"Seat {s.seat_code} is currently held by another customer")
        
        redis_hold = redis_manager.get_seat_hold(event_id, s.seat_code)
        if redis_hold and redis_hold.get("user_id") != user_id:
            raise HTTPException(status_code=400, detail=f"Seat {s.seat_code} is currently held by another customer")

    hold_expires = now + timedelta(minutes=10)
    for s in target_seats:
        s.status = "HELD"
        s.held_by_user_id = user_id
        s.held_until = hold_expires
        redis_manager.set_seat_hold(event_id, s.seat_code, user_id, ttl_seconds=600)

    db.commit()
    return target_seats


def get_event_seat_map(db: Session, event_id: int) -> Dict[str, Any]:
    """
    Returns seat map categorized by section with real-time status.
    Auto-initializes seats if none exist yet.
    """
    seats = db.query(Seat).filter(Seat.event_id == event_id).all()
    if not seats:
        initialize_event_seats(db, event_id)
        seats = db.query(Seat).filter(Seat.event_id == event_id).all()

    now = datetime.utcnow()
    result = {}
    for s in seats:
        # Check expired hold
        status = s.status
        if status == "HELD" and s.held_until and s.held_until < now:
            status = "AVAILABLE"

        sec_name = s.section_name or "Main Floor"
        if sec_name not in result:
            result[sec_name] = []
        result[sec_name].append({
            "id": s.id,
            "event_id": s.event_id,
            "section_name": sec_name,
            "row_label": s.row_label,
            "seat_number": s.seat_number,
            "seat_code": s.seat_code,
            "status": status,
            "price": s.price
        })
    return result
