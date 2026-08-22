from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.ticket import Event
from app.models.ticket_tier import TicketTier
from app.services.tier_inventory_service import (
    create_or_update_event_tiers,
    sync_event_capacity_from_tiers
)

router = APIRouter()

@router.get("/events/{event_id}/tiers")
def list_event_tiers(event_id: int, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail={"code": "EVENT_NOT_FOUND", "message": "Event not found"})

    tiers = db.query(TicketTier).filter(TicketTier.event_id == event_id).all()

    # Auto-initialize fallback tier if none configured yet
    if not tiers:
        default_tier = TicketTier(
            event_id=event.id,
            name="General Admission",
            price=event.price or 0.0,
            total_quantity=event.total_capacity or 100,
            available_quantity=event.available_tickets or 100,
            held_quantity=0,
            sold_quantity=max(0, (event.total_capacity or 100) - (event.available_tickets or 100)),
            min_per_order=1,
            max_per_order=event.max_tickets_per_booking or 10
        )
        db.add(default_tier)
        db.commit()
        db.refresh(default_tier)
        tiers = [default_tier]

    result = []
    for t in tiers:
        status = "AVAILABLE"
        if t.available_quantity <= 0:
            status = "SOLD_OUT"
        elif t.available_quantity <= 5:
            status = "LOW_STOCK"

        result.append({
            "id": t.id,
            "event_id": t.event_id,
            "name": t.name,
            "price": t.price,
            "total_quantity": t.total_quantity,
            "available_quantity": t.available_quantity,
            "held_quantity": t.held_quantity,
            "sold_quantity": t.sold_quantity,
            "min_per_order": t.min_per_order,
            "max_per_order": t.max_per_order,
            "status": status,
            "sales_start": t.sales_start.isoformat() if t.sales_start else None,
            "sales_end": t.sales_end.isoformat() if t.sales_end else None
        })

    summary = {
        "event_id": event_id,
        "total_capacity": sum(t["total_quantity"] for t in result),
        "total_sold": sum(t["sold_quantity"] for t in result),
        "total_held": sum(t["held_quantity"] for t in result),
        "total_available": sum(t["available_quantity"] for t in result),
        "tiers": result
    }
    return summary

@router.post("/events/{event_id}/tiers")
def configure_event_tiers(event_id: int, payload: Dict[str, Any], db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail={"code": "EVENT_NOT_FOUND", "message": "Event not found"})

    tier_list = payload.get("tiers") or payload.get("ticket_types") or []
    updated_tiers = create_or_update_event_tiers(db, event, tier_list)
    return {"message": "Ticket tiers configured successfully", "event_id": event_id, "tiers": updated_tiers}

@router.put("/events/{event_id}/tiers/{tier_id}")
def update_single_tier(event_id: int, tier_id: int, payload: Dict[str, Any], db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail={"code": "EVENT_NOT_FOUND", "message": "Event not found"})

    payload["id"] = tier_id
    updated = create_or_update_event_tiers(db, event, [payload])
    return {"message": "Tier updated successfully", "tier": updated[0]}
