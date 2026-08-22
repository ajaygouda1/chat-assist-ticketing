from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.ticket import Event
from app.models.refund import RefundPolicy
from app.schemas.schemas import EventCompareRequest

router = APIRouter()

@router.post("/events/compare")
def compare_events(req: EventCompareRequest, db: Session = Depends(get_db)):
    if not req.event_ids or len(req.event_ids) < 2:
        raise HTTPException(status_code=400, detail="Select at least 2 events to compare")

    events = db.query(Event).filter(Event.id.in_(req.event_ids)).all()
    comparison_table = []

    for ev in events:
        policy = db.query(RefundPolicy).filter(RefundPolicy.event_id == ev.id).first()
        policy_str = policy.policy_type if policy else "FLEXIBLE"
        
        comparison_table.append({
            "id": ev.id,
            "title": ev.title,
            "price": ev.price,
            "category": ev.category,
            "location": ev.location,
            "date": ev.date_str,
            "available_tickets": ev.available_tickets,
            "total_capacity": ev.total_capacity,
            "refund_policy": policy_str,
            "certificate_provided": "Yes" if "workshop" in ev.title.lower() or "ai" in ev.title.lower() else "No",
            "food_included": "Refreshments Provided" if ev.price > 400 else "Available at venue"
        })

    # Generate grounded AI synthesis note based strictly on comparison data
    cheapest = min(events, key=lambda x: x.price) if events else None
    ai_note = f"Grounding Analysis: {cheapest.title if cheapest else 'N/A'} is the most budget-friendly option at ₹{cheapest.price if cheapest else 0}."

    return {
        "events": comparison_table,
        "ai_recommendation_note": ai_note
    }
