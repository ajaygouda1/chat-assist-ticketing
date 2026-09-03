import uuid
from typing import Dict, Any, List, Optional

from app.ai.schemas import AgentResponse, UIComponent, ConversationStateSnapshot
from app.ai.conversation_memory import ConversationState

def build_agent_response(
    message: str,
    state: ConversationState,
    primary_tool_name: Optional[str] = None,
    primary_tool_data: Optional[Dict[str, Any]] = None,
    quick_replies: Optional[List[Dict[str, str]]] = None,
    intent: Optional[str] = "ai_agent"
) -> AgentResponse:
    ui_components: List[UIComponent] = []
    card_type = "text"
    card_payload: Optional[Dict[str, Any]] = None

    if primary_tool_name == "search_events" and primary_tool_data:
        events = primary_tool_data.get("events", [])
        if events:
            card_type = "event_results"
            card_payload = {"events": events}
            ui_components.append(UIComponent(type="event_carousel", data={"events": events}))
            if not quick_replies:
                quick_replies = [
                    {"label": f"Book {events[0]['title'][:18]}", "text": f"Book tickets for {events[0]['title']}"}
                ]
                if len(events) > 1:
                    quick_replies.append({"label": f"Book {events[1]['title'][:18]}", "text": f"Book tickets for {events[1]['title']}"})

    elif primary_tool_name in ["create_booking_draft", "update_booking_draft"] and primary_tool_data:
        card_type = "booking_summary"
        card_payload = primary_tool_data
        ui_components.append(UIComponent(type="booking_summary", data=primary_tool_data))
        total_inr = primary_tool_data.get("total", 0.0)
        if not quick_replies:
            quick_replies = [
                {"label": f"✅ Confirm & Pay ₹{total_inr:.2f}", "text": "Confirm booking and proceed to pay"},
                {"label": "❌ Cancel Reservation", "text": "Cancel my booking"}
            ]

    elif primary_tool_name == "create_payment_order" and primary_tool_data:
        card_type = "payment_button"
        card_payload = primary_tool_data.get("payment_payload", {})
        ui_components.append(UIComponent(type="payment_button", data=card_payload))

    elif primary_tool_name == "get_user_tickets" and primary_tool_data:
        tickets = primary_tool_data.get("tickets", [])
        if tickets:
            card_type = "my_tickets_list"
            card_payload = {"tickets": tickets}
            ui_components.append(UIComponent(type="my_tickets_list", data={"tickets": tickets}))

    elif primary_tool_name == "cancel_booking" and primary_tool_data:
        card_type = "cancellation_card"
        card_payload = primary_tool_data
        ui_components.append(UIComponent(type="cancellation_card", data=primary_tool_data))

    elif primary_tool_name == "apply_promo_code" and primary_tool_data:
        card_type = "booking_summary"
        card_payload = primary_tool_data
        ui_components.append(UIComponent(type="booking_summary", data=primary_tool_data))

    elif primary_tool_name == "compare_events" and primary_tool_data:
        card_type = "comparison_card"
        card_payload = primary_tool_data
        ui_components.append(UIComponent(type="comparison_card", data=primary_tool_data))

    elif primary_tool_name == "get_event_recommendations" and primary_tool_data:
        recs = primary_tool_data.get("recommendations", [])
        if recs:
            card_type = "event_results"
            card_payload = {"events": recs}
            ui_components.append(UIComponent(type="event_carousel", data={"events": recs}))

    # If greeting or idle general chat without a tool
    if not primary_tool_name and not quick_replies:
        msg_lower = message.lower()
        if any(w in msg_lower for w in ["hi", "hello", "hey", "welcome", "help", "what can you do"]):
            quick_replies = [
                {"label": "🔍 Explore Live Events", "text": "Show live upcoming events in Bengaluru"},
                {"label": "🎟️ My Tickets", "text": "Show my tickets"},
                {"label": "🎤 Create Event", "text": "I want to create an event"}
            ]

    message_id = f"msg_{uuid.uuid4().hex[:12]}"

    return AgentResponse(
        conversation_id=state.conversation_id,
        message_id=message_id,
        message=message,
        reply=message,  # Backward-compatible alias
        ui=ui_components,
        state=state.to_dict(),
        type=card_type,
        payload=card_payload,
        quick_replies=quick_replies,
        intent=intent,
        grounding_status="GROUNDED_LIVE_DB"
    )
