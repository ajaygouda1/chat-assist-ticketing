import json
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.ticket import Event
from app.ai.system_prompt import SYSTEM_PROMPT
from app.ai.conversation_memory import ConversationState

def build_ai_context(
    state: ConversationState,
    history: List[Dict[str, Any]],
    user_role: str = "customer",
    db: Optional[Session] = None
) -> List[Dict[str, Any]]:
    """
    Constructs bounded prompt context combining system guidelines,
    user role, grounded state, and conversation history.
    """
    system_content = SYSTEM_PROMPT + f"\n\n## Authenticated User Context:\n- Role: {user_role}\n- User ID: {state.user_id}\n"

    # Add active state grounding
    grounded_info = []
    if state.selected_event_id and db:
        ev = db.query(Event).filter(Event.id == state.selected_event_id).first()
        if ev:
            grounded_info.append(f"Active Selected Event: ID={ev.id}, Title='{ev.title}', Venue='{ev.venue or ev.location}', Date='{ev.date_str}', BasePrice=₹{ev.price}, AvailableSeats={ev.available_tickets}")

    if state.selected_tier_name:
        grounded_info.append(f"Active Selected Tier: {state.selected_tier_name}")

    if state.quantity:
        grounded_info.append(f"Active Quantity: {state.quantity}")

    if state.booking_draft_id:
        grounded_info.append(f"Active Booking Draft ID: {state.booking_draft_id}")

    if state.active_hold_expires_at:
        grounded_info.append(f"Active Hold Expiration: {state.active_hold_expires_at.isoformat()}")

    if state.last_event_result_ids and db:
        recent_events = db.query(Event).filter(Event.id.in_(state.last_event_result_ids)).all()
        recent_map = {e.id: e for e in recent_events}
        results_summary = []
        for idx, eid in enumerate(state.last_event_result_ids):
            if eid in recent_map:
                e = recent_map[eid]
                results_summary.append(f"[{idx + 1}] ID={e.id} '{e.title}' at {e.location} (₹{e.price})")
        if results_summary:
            grounded_info.append("Last Search Results (for resolving 'first one', 'second one', etc.):\n" + "\n".join(results_summary))

    if grounded_info:
        system_content += "\n## Current Grounded Session State:\n" + "\n".join(grounded_info)

    messages = [{"role": "system", "content": system_content}]

    # Append recent conversation history
    for msg in history:
        messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })

    return messages
