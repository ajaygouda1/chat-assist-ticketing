from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.ticket import Event
from app.models.ticket_tier import TicketTier
from app.models.seating import Seat
from app.core.redis import redis_manager

def validate_tier_inputs(name: str, price: float, total_quantity: int, min_per_order: int, max_per_order: int, sales_start: Optional[datetime] = None, sales_end: Optional[datetime] = None):
    if not name or len(name.strip()) == 0:
        raise HTTPException(status_code=400, detail={"code": "INVALID_TIER_NAME", "message": "Tier name cannot be empty."})

    if price is None or price < 0:
        raise HTTPException(status_code=400, detail={"code": "INVALID_PRICE", "message": f"Tier '{name}' price cannot be negative."})

    if total_quantity is None or total_quantity <= 0:
        raise HTTPException(status_code=400, detail={"code": "INVALID_QUANTITY", "message": f"Tier '{name}' total quantity must be greater than 0."})

    if min_per_order < 1:
        raise HTTPException(status_code=400, detail={"code": "INVALID_ORDER_LIMIT", "message": f"Tier '{name}' min tickets per order must be at least 1."})

    if max_per_order < min_per_order:
        raise HTTPException(status_code=400, detail={"code": "INVALID_ORDER_LIMIT", "message": f"Tier '{name}' max per order ({max_per_order}) cannot be less than min per order ({min_per_order})."})

    if max_per_order > total_quantity:
        raise HTTPException(status_code=400, detail={"code": "INVALID_ORDER_LIMIT", "message": f"Tier '{name}' max per order ({max_per_order}) cannot exceed total quantity ({total_quantity})."})

    if sales_start and sales_end and sales_end < sales_start:
        raise HTTPException(status_code=400, detail={"code": "INVALID_SALES_DATES", "message": f"Tier '{name}' sales end date cannot be before sales start date."})

def sync_event_capacity_from_tiers(db: Session, event: Event):
    tiers = db.query(TicketTier).filter(TicketTier.event_id == event.id).all()
    if tiers:
        event.total_capacity = sum(t.total_quantity for t in tiers)
        event.available_tickets = sum(t.available_quantity for t in tiers)
        if not event.price or event.price == 0:
            event.price = min(t.price for t in tiers)
        db.commit()

def create_or_update_event_tiers(db: Session, event: Event, tier_data_list: List[Dict[str, Any]]) -> List[TicketTier]:
    """
    Creates or updates ticket tiers for an event. Enforces quantity adjustment rules
    and keeps event total_capacity and available_tickets synced.
    """
    if not tier_data_list or len(tier_data_list) == 0:
        raise HTTPException(status_code=400, detail={"code": "EMPTY_TIERS", "message": "Event must have at least one ticket tier."})

    # Check if reserved seating exists for this event
    seats = db.query(Seat).filter(Seat.event_id == event.id).all()
    
    existing_tiers = {t.id: t for t in db.query(TicketTier).filter(TicketTier.event_id == event.id).all()}
    existing_by_name = {t.name.lower().strip(): t for t in existing_tiers.values()}

    result_tiers = []

    for item in tier_data_list:
        name = str(item.get("name", "Standard Pass")).strip()
        price = float(item.get("price", 0.0))
        total_quantity = int(item.get("total_quantity") if item.get("total_quantity") is not None else (item.get("quantity") if item.get("quantity") is not None else 50))

        min_per_order = int(item.get("min_per_order", 1))
        max_per_order = int(item.get("max_per_order", 10))
        sales_start = item.get("sales_start")
        sales_end = item.get("sales_end")

        if seats:
            matching_seats = [s for s in seats if (s.section_name or "").lower().strip() in name.lower() or name.lower() in (s.section_name or "").lower()]
            if matching_seats and total_quantity != len(matching_seats):
                raise HTTPException(
                    status_code=400,
                    detail={
                        "code": "RESERVED_SEAT_MISMATCH",
                        "message": f"Reserved seating tier '{name}' quantity ({total_quantity}) must match physical seat count ({len(matching_seats)})."
                    }
                )

        tier_id = item.get("id")

        existing = existing_tiers.get(tier_id) if tier_id else existing_by_name.get(name.lower().strip())

        if existing:
            # Editing existing tier
            old_total = existing.total_quantity
            sold = existing.sold_quantity or 0
            held = existing.held_quantity or 0
            minimum_allowed = sold + held

            if total_quantity < minimum_allowed:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "code": "CANNOT_REDUCE_BELOW_SOLD",
                        "message": f"Cannot reduce ticket quantity for '{name}' below already sold ({sold}) or held ({held}) tickets (minimum allowed: {minimum_allowed})."
                    }
                )

            max_per_order = min(max_per_order, total_quantity)
            validate_tier_inputs(name, price, total_quantity, min_per_order, max_per_order, sales_start, sales_end)
            delta = total_quantity - old_total
            existing.name = name
            existing.price = price
            existing.total_quantity = total_quantity
            existing.available_quantity += delta
            existing.min_per_order = min_per_order
            existing.max_per_order = max_per_order
            existing.sales_start = sales_start
            existing.sales_end = sales_end
            result_tiers.append(existing)
        else:
            max_per_order = min(max_per_order, total_quantity)
            validate_tier_inputs(name, price, total_quantity, min_per_order, max_per_order, sales_start, sales_end)
            # Creating new tier
            new_tier = TicketTier(
                event_id=event.id,
                name=name,
                price=price,
                total_quantity=total_quantity,
                available_quantity=total_quantity,
                held_quantity=0,
                sold_quantity=0,
                min_per_order=min_per_order,
                max_per_order=max_per_order,
                sales_start=sales_start,
                sales_end=sales_end
            )
            db.add(new_tier)
            result_tiers.append(new_tier)



    db.commit()
    for t in result_tiers:
        db.refresh(t)

    sync_event_capacity_from_tiers(db, event)
    return result_tiers

def hold_tier_inventory(db: Session, event_id: int, tier_name_or_id: Any, requested_qty: int, user_id: int) -> TicketTier:
    """
    Atomically holds inventory for a ticket tier.
    Moves requested_qty from available_quantity -> held_quantity.
    """
    if requested_qty <= 0:
        raise HTTPException(status_code=400, detail={"code": "INVALID_QUANTITY", "message": "Requested ticket quantity must be at least 1."})

    query = db.query(TicketTier).filter(TicketTier.event_id == event_id)
    if isinstance(tier_name_or_id, int):
        query = query.filter(TicketTier.id == tier_name_or_id)
    else:
        query = query.filter(TicketTier.name.ilike(f"%{str(tier_name_or_id).strip()}%"))

    tier = query.with_for_update().first()
    if not tier:
        # Fallback if no specific tier match: pick first available tier
        tier = db.query(TicketTier).filter(TicketTier.event_id == event_id).with_for_update().first()

    if not tier:
        raise HTTPException(status_code=404, detail={"code": "TIER_NOT_FOUND", "message": f"No ticket tier found for event #{event_id}."})

    if requested_qty < tier.min_per_order:
        raise HTTPException(
            status_code=400,
            detail={"code": "BELOW_MIN_ORDER", "message": f"Minimum order for '{tier.name}' is {tier.min_per_order} ticket(s)."}
        )

    if requested_qty > tier.max_per_order:
        raise HTTPException(
            status_code=400,
            detail={"code": "EXCEEDS_MAX_ORDER", "message": f"Maximum order for '{tier.name}' is {tier.max_per_order} ticket(s)."}
        )

    # Atomic inventory update query
    rows_updated = db.query(TicketTier).filter(
        TicketTier.id == tier.id,
        TicketTier.available_quantity >= requested_qty
    ).update({
        TicketTier.available_quantity: TicketTier.available_quantity - requested_qty,
        TicketTier.held_quantity: TicketTier.held_quantity + requested_qty
    })

    if rows_updated == 0:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INSUFFICIENT_TICKETS",
                "message": f"Only {tier.available_quantity} {tier.name} ticket(s) currently available."
            }
        )

    ev = db.query(Event).filter(Event.id == event_id).first()
    if ev and ev.available_tickets >= requested_qty:
        ev.available_tickets -= requested_qty

    db.commit()
    db.refresh(tier)

    # Also register Redis hold key for lock propagation
    redis_manager.client.set(f"tier_hold:{event_id}:{tier.id}:{user_id}", requested_qty, ex=600)

    return tier

def confirm_tier_inventory_payment(db: Session, event_id: int, tier_name_or_id: Any, qty: int):
    """
    Moves inventory from held_quantity -> sold_quantity upon payment confirmation.
    """
    query = db.query(TicketTier).filter(TicketTier.event_id == event_id)
    if isinstance(tier_name_or_id, int):
        query = query.filter(TicketTier.id == tier_name_or_id)
    elif tier_name_or_id:
        query = query.filter(TicketTier.name.ilike(f"%{str(tier_name_or_id).strip()}%"))

    tier = query.with_for_update().first()
    if not tier:
        tier = db.query(TicketTier).filter(TicketTier.event_id == event_id).with_for_update().first()

    if tier:
        actual_held = min(tier.held_quantity, qty)
        tier.held_quantity -= actual_held
        tier.sold_quantity += qty
        db.commit()

def release_tier_inventory_hold(db: Session, event_id: int, tier_name_or_id: Any, qty: int):
    """
    Restores inventory from held_quantity -> available_quantity when hold expires or is cancelled.
    """
    query = db.query(TicketTier).filter(TicketTier.event_id == event_id)
    if isinstance(tier_name_or_id, int):
        query = query.filter(TicketTier.id == tier_name_or_id)
    elif tier_name_or_id:
        query = query.filter(TicketTier.name.ilike(f"%{str(tier_name_or_id).strip()}%"))

    tier = query.with_for_update().first()
    if not tier:
        tier = db.query(TicketTier).filter(TicketTier.event_id == event_id).with_for_update().first()

    if tier:
        actual_held = min(tier.held_quantity, qty)
        tier.held_quantity -= actual_held
        tier.available_quantity += qty

        ev = db.query(Event).filter(Event.id == event_id).first()
        if ev:
            ev.available_tickets += qty

        db.commit()
