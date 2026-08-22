import os
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.ticket import Event, Ticket
from app.ml.intent_router import intent_router
from app.services.booking_conversation import get_booking_session, BookingState, handle_book_ticket_turn

class AIService:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY", "")

    def _call_llm_fallback(self, message: str, db: Session) -> str:
        api_key = os.getenv("OPENAI_API_KEY", "") or self.api_key
        if api_key:
            try:
                import httpx
                resp = httpx.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={
                        "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                        "messages": [
                            {"role": "system", "content": "You are ChatAssist, a helpful event ticketing assistant. Keep answers brief, accurate, and friendly."},
                            {"role": "user", "content": message}
                        ],
                        "max_tokens": 150
                    },
                    timeout=5.0
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return data["choices"][0]["message"]["content"].strip()
            except Exception as e:
                print(f"OpenAI LLM Fallback notice: {e}")

        # Grounded fallback if OpenAI API key is missing or call fails
        events = db.query(Event).filter(Event.available_tickets > 0).limit(2).all()
        if events:
            return f"I'm ChatAssist! You can ask me to search live events in Bengaluru, book passes, or manage your tickets. How can I help you today?"

        return "I'm ChatAssist! I can help you search events, book tickets, check invoices, or handle refunds. How can I assist you today?"

    def process_chat_message(
        self,
        message: str,
        user_id: int,
        db: Session,
        event_type: str = "user_message",
        payload: Optional[Dict[str, Any]] = None,
        conversation_id: Optional[int] = None
    ) -> dict:
        """
        Process incoming user chat message or system event with Intent Router + Live DB Grounding.
        """
        msg_lower = (message or "").lower().strip()
        session = get_booking_session(user_id, conversation_id)

        # Handle system event directly
        if event_type == "system_event" or (payload and payload.get("event") == "PAYMENT_VERIFIED"):
            from app.ml.slot_extractor import extract_event_slots
            slots = extract_event_slots(message or "")
            res = handle_book_ticket_turn(user_id, message, slots, db, event_type, payload, conversation_id)
            res["mode"] = session.mode.value
            res["fsm_state"] = session.state.value
            return res

        # Step 1: Intent Routing via ML classifier
        routing_res = intent_router.route_intent(message)
        intent = routing_res["intent"]
        confidence = routing_res["confidence"]
        routed_to = routing_res["routed_to"]

        # Step 2: Event Creation Intent Check & Mode Transition
        is_create_request = intent == "create_event" or any(k in msg_lower for k in ["create event", "create an event", "create a workshop", "organize an event", "tech workshop"])
        if is_create_request:
            session.reset()
            from app.services.booking_conversation import handle_create_event_turn
            res = handle_create_event_turn(user_id, message, db, conversation_id)
            res["confidence"] = confidence
            return res

        # Step 3: Session state check & explicit reset/cancellation
        if any(k in msg_lower for k in ["cancel", "reset", "start over", "abort"]):
            if session.state != BookingState.IDLE:
                session.reset()
                return {
                    "reply": "Booking cancelled. Your held seats have been released.",
                    "intent": "cancel_ticket",
                    "confidence": 0.99,
                    "routed_to": "BOOKING_STATE_MACHINE",
                    "grounding_status": "GROUNDED_LIVE_DB",
                    "mode": session.mode.value,
                    "fsm_state": session.state.value,
                    "type": "text",
                    "payload": None,
                    "quick_replies": [
                        {"label": "🔍 Find Events", "text": "Show live upcoming events"},
                        {"label": "🎟️ My Tickets", "text": "Show my tickets"}
                    ]
                }
            intent = "cancel_ticket"

        elif session.state != BookingState.IDLE and intent in ["search_event", "view_tickets", "create_event"] and confidence >= 0.40:
            session.reset()

        # Handle active booking flow
        if intent == "book_ticket" or (session.state != BookingState.IDLE and intent not in ["search_event", "view_tickets", "cancel_ticket", "create_event"]):
            from app.ml.slot_extractor import extract_event_slots
            slots = extract_event_slots(message)
            res = handle_book_ticket_turn(user_id, message, slots, db, event_type, payload, conversation_id)
            res["mode"] = session.mode.value
            res["fsm_state"] = session.state.value
            return res

        # Handle deterministic intent routes directly from DB with 100% grounding
        grounding_status = "GROUNDED_LIVE_DB"
        reply = ""
        quick_replies = None
        card_type = "text"
        card_payload = None

        if intent == "greeting":
            reply = "Hi! I can help you discover events, book tickets, view your bookings, handle refunds, or create your own event.\n\nWhat would you like to do?"
            quick_replies = [
                {"label": "🔍 Explore Events", "text": "Show live upcoming events"},
                {"label": "🎟️ My Tickets", "text": "Show my tickets"},
                {"label": "✨ Create Event", "text": "Create Event"}
            ]

        elif intent == "search_event":
            import re
            query = db.query(Event).filter(Event.available_tickets > 0, Event.status == "PUBLISHED")

            # Extract category filter
            cat_match = None
            for cat in ["technology", "tech", "ai", "artificial intelligence", "workshop", "music", "gaming", "sports", "business"]:
                if cat in msg_lower:
                    cat_match = cat
                    break
            if cat_match:
                if cat_match in ["tech", "technology"]:
                    query = query.filter(Event.category.ilike("%Tech%") | Event.category.ilike("%Technology%"))
                elif cat_match in ["ai", "artificial intelligence"]:
                    query = query.filter(Event.category.ilike("%AI%") | Event.title.ilike("%AI%"))
                else:
                    query = query.filter(Event.category.ilike(f"%{cat_match}%"))

            # Extract price filter
            price_match = re.search(r'(?:under|below|less than|<=|<|\b₹?\s*)(\d+)', msg_lower)
            if price_match:
                max_p = float(price_match.group(1))
                if max_p > 0 and "tickets" not in msg_lower:
                    query = query.filter(Event.price <= max_p)

            # Extract city / location filter
            for city in ["bengaluru", "bangalore", "mangaluru", "mangalore"]:
                if city in msg_lower:
                    target_city = "Bengaluru" if "beng" in city or "bang" in city else "Mangaluru"
                    query = query.filter(Event.location.ilike(f"%{target_city}%"))
                    break

            events = query.all()
            if not events and (cat_match or price_match):
                # Fallback to all published live events if overly restrictive filter
                events = db.query(Event).filter(Event.available_tickets > 0, Event.status == "PUBLISHED").all()

            if events:
                session.last_event_results = [e.id for e in events]
                reply = f"I found {len(events)} event{'s' if len(events)>1 else ''} matching your search."
                card_type = "event_results"
                card_payload = {
                    "events": [
                        {
                            "id": e.id,
                            "title": e.title,
                            "category": e.category,
                            "date_str": e.date_str,
                            "location": e.location,
                            "price": e.price,
                            "available_tickets": e.available_tickets,
                            "image_url": e.image_url
                        } for e in events[:6]
                    ]
                }
                quick_replies = [
                    {"label": f"Book {events[0].title[:18]}", "text": f"Book ticket for {events[0].title}"}
                ] if events else None
            else:
                reply = "Currently there are no active events matching your search criteria."
                quick_replies = [{"label": "Show all events", "text": "Show live upcoming events"}]

        elif intent == "event_faq":
            target_event = None
            if session.event_id:
                target_event = db.query(Event).filter(Event.id == session.event_id).first()
            elif session.last_event_results:
                target_event = db.query(Event).filter(Event.id == session.last_event_results[0]).first()
            else:
                target_event = db.query(Event).filter(Event.available_tickets > 0).first()

            if not target_event:
                reply = "That information hasn't been provided by the organizer."
            else:
                desc = (target_event.description or "").lower()
                cancellation = (target_event.cancellation_policy or "").lower()
                features = [f.lower() for f in (target_event.tags or target_event.ticket_types or [])] if isinstance(target_event.tags, list) else []

                if any(k in msg_lower for k in ["venue", "where", "location", "address"]):
                    venue_info = target_event.venue or target_event.location
                    reply = f"The venue for **{target_event.title}** is {venue_info} ({target_event.location})."
                elif any(k in msg_lower for k in ["time", "start", "end", "when"]):
                    reply = f"**{target_event.title}** takes place on {target_event.date_str} from {target_event.start_time or '10:00'} to {target_event.end_time or '16:00'}."
                elif "certificate" in msg_lower:
                    if "certificate" in desc or "certificate" in features or "certificate" in str(target_event.tags).lower():
                        reply = f"Yes, certificates are provided for participants attending **{target_event.title}**."
                    else:
                        reply = "That information hasn't been provided by the organizer."
                elif any(k in msg_lower for k in ["food", "lunch", "meal", "refreshment"]):
                    if any(k in desc for k in ["food", "lunch", "meal", "refreshment"]):
                        reply = f"Yes, food/refreshments are included for **{target_event.title}**."
                    else:
                        reply = "That information hasn't been provided by the organizer."
                elif any(k in msg_lower for k in ["student", "can students", "eligibility"]):
                    if "student" in desc or "open to all" in desc:
                        reply = f"Yes, students are welcome to attend **{target_event.title}**."
                    else:
                        reply = "That information hasn't been provided by the organizer."
                else:
                    reply = "That information hasn't been provided by the organizer."

        elif intent == "compare_events":
            compare_ids = session.last_event_results[:2] if session.last_event_results and len(session.last_event_results) >= 2 else []
            if not compare_ids:
                all_evs = db.query(Event).filter(Event.available_tickets > 0, Event.status == "PUBLISHED").limit(2).all()
                compare_ids = [e.id for e in all_evs]

            if len(compare_ids) >= 2:
                ev1 = db.query(Event).filter(Event.id == compare_ids[0]).first()
                ev2 = db.query(Event).filter(Event.id == compare_ids[1]).first()
                if ev1 and ev2:
                    reply = f"### Event Comparison\n\n| Feature | {ev1.title[:20]} | {ev2.title[:20]} |\n|---|---|---|\n| **Price** | ₹{ev1.price:.0f} | ₹{ev2.price:.0f} |\n| **Location** | {ev1.location} | {ev2.location} |\n| **Date** | {ev1.date_str} | {ev2.date_str} |\n| **Seats Left** | {ev1.available_tickets} | {ev2.available_tickets} |\n\n💡 *{ev1.title}* is priced at ₹{ev1.price:.0f}, while *{ev2.title}* has {ev2.available_tickets} seats remaining."
                else:
                    reply = "Select at least two events from search to compare."
            else:
                reply = "Please search events first to compare them."

        elif intent == "view_tickets":
            tickets = db.query(Ticket).filter(Ticket.user_id == user_id).all()
            if tickets:
                ticket_list = []
                for t in tickets:
                    ev = db.query(Event).filter(Event.id == t.event_id).first()
                    ticket_list.append({
                        "ticket_id": t.id,
                        "ticket_number": t.ticket_number,
                        "event_title": ev.title if ev else "Event Ticket",
                        "price_paid": t.price_paid,
                        "status": t.status,
                        "date_str": ev.date_str if ev else "",
                        "location": ev.location if ev else ""
                    })
                reply = f"Here are your booked passes:"
                card_type = "my_tickets_list"
                card_payload = {"tickets": ticket_list}
                quick_replies = [{"label": "Explore More Events", "text": "Show live upcoming events"}]
            else:
                reply = "You don't have any booked tickets yet. Would you like to explore upcoming events?"
                quick_replies = [{"label": "Explore Events", "text": "Show live upcoming events"}]

        elif intent == "cancel_ticket":
            tickets = db.query(Ticket).filter(Ticket.user_id == user_id, Ticket.status == "CONFIRMED").all()
            if tickets:
                t = tickets[0]
                ev = db.query(Event).filter(Event.id == t.event_id).first()
                reply = f"I found this ticket eligible for cancellation:"
                card_type = "cancellation_card"
                card_payload = {
                    "ticket_id": t.id,
                    "ticket_number": t.ticket_number,
                    "event_title": ev.title if ev else "Event",
                    "price_paid": t.price_paid
                }
                quick_replies = [
                    {"label": "Confirm Cancellation", "text": f"Cancel ticket {t.ticket_number}"},
                    {"label": "Keep Ticket", "text": "Keep my ticket"}
                ]
            else:
                reply = "You have no active confirmed tickets eligible for cancellation."
                quick_replies = [{"label": "Explore Events", "text": "Show live upcoming events"}]

        elif intent == "transfer_ticket":
            tickets = db.query(Ticket).filter(Ticket.user_id == user_id, Ticket.status == "CONFIRMED").all()
            if tickets:
                t = tickets[0]
                ev = db.query(Event).filter(Event.id == t.event_id).first()
                reply = f"You can transfer pass **{t.ticket_number}** for *{ev.title if ev else 'Event'}* to a friend. Please enter their email address in the My Tickets panel or click Transfer Ticket on your confirmed pass."
            else:
                reply = "You have no active tickets available for transfer."

        elif intent == "create_event":
            from app.services.booking_conversation import handle_create_event_turn
            return handle_create_event_turn(user_id, message, db, conversation_id)

        else:
            # Fallback for General Chat / LLM Reasoning
            grounding_status = "LLM_REASONED"
            reply = self._call_llm_fallback(message, db)
            quick_replies = [
                {"label": "Explore Events", "text": "Show live upcoming events"},
                {"label": "My Tickets", "text": "Show my tickets"},
                {"label": "Create Event", "text": "Create Event"}
            ]

        return {
            "reply": reply,
            "intent": intent,
            "confidence": confidence,
            "routed_to": routed_to,
            "grounding_status": grounding_status,
            "type": card_type,
            "payload": card_payload,
            "quick_replies": quick_replies
        }

ai_service = AIService()



