import os
from sqlalchemy.orm import Session
from app.models.ticket import Event, Ticket
from app.ml.intent_router import intent_router
from app.services.booking_conversation import get_booking_session, BookingState

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
                            {"role": "system", "content": "You are ChatAssist AI Copilot, a helpful event ticketing assistant. Keep answers brief, accurate, and friendly."},
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

        # Intelligent grounded fallback if OpenAI API key is missing or call fails
        events = db.query(Event).filter(Event.available_tickets > 0).limit(2).all()
        if events:
            titles = ", ".join([f"'{e.title}'" for e in events])
            return f"I'm ChatAssist AI Copilot! We currently have active events like {titles}. You can ask me to search events, book tickets, view your passes, or request refunds. How can I help you?"

        return "I'm your ChatAssist AI Copilot! I can help you search events, book tickets, check invoices, or handle refunds. How can I assist you today?"

    def process_chat_message(self, message: str, user_id: int, db: Session) -> dict:
        """
        Process incoming user chat message with Intent Router + Live DB Grounding.
        """
        msg_lower = message.lower().strip()

        # Step 1: Intent Routing via ML classifier
        routing_res = intent_router.route_intent(message)
        intent = routing_res["intent"]
        confidence = routing_res["confidence"]
        routed_to = routing_res["routed_to"]

        # Step 2: Session state check
        session = get_booking_session(user_id)
        
        # If user explicitly asks for cancel/reset or another distinct high-confidence intent, break out of booking session
        if any(k in msg_lower for k in ["cancel", "reset", "start over", "abort"]):
            session.reset()
        elif session.state != BookingState.IDLE and intent in ["search_event", "view_tickets", "cancel_ticket", "create_event"] and confidence >= 0.40:
            session.reset()

        # Handle active booking flow
        if intent == "book_ticket" or (session.state != BookingState.IDLE and intent not in ["search_event", "view_tickets", "cancel_ticket", "create_event"]):
            from app.ml.slot_extractor import extract_event_slots
            from app.services.booking_conversation import handle_book_ticket_turn
            
            slots = extract_event_slots(message)
            return handle_book_ticket_turn(user_id, message, slots, db)

        # Handle deterministic intent routes directly from DB with 100% grounding
        grounding_status = "GROUNDED_LIVE_DB"
        reply = ""

        quick_replies = None
        card_type = "text"
        card_payload = None

        if intent == "search_event":
            events = db.query(Event).filter(Event.available_tickets > 0, Event.status == "PUBLISHED").all()
            if events:
                event_list = "\n".join([f"• **{e.title}** ({e.category}) - ₹{e.price:.0f} | {e.available_tickets} seats left | {e.location}" for e in events[:4]])
                reply = f"Here are live events available right now:\n\n{event_list}\n\nTap a button below to book tickets or choose an option:"
                quick_replies = [{"label": f"Book {e.title[:18]}", "text": f"Book ticket for {e.title}"} for e in events[:3]]
            else:
                reply = "Currently there are no active events with open tickets."

        elif intent == "view_tickets":
            tickets = db.query(Ticket).filter(Ticket.user_id == user_id).all()
            if tickets:
                t_details = []
                for t in tickets:
                    ev = db.query(Event).filter(Event.id == t.event_id).first()
                    ev_title = ev.title if ev else "Event"
                    t_details.append(f"• Ticket **{t.ticket_number}** for *{ev_title}* (Status: `{t.status}`) - Price: ₹{t.price_paid:.2f}")
                reply = f"Here are your confirmed bookings:\n\n" + "\n".join(t_details)
                quick_replies = [{"label": "Explore More Events", "text": "Show live upcoming events"}]
            else:
                reply = "You don't have any booked tickets yet. Would you like to explore upcoming events?"
                quick_replies = [{"label": "Explore Events", "text": "Show live upcoming events"}]

        elif intent == "cancel_ticket":
            tickets = db.query(Ticket).filter(Ticket.user_id == user_id, Ticket.status == "CONFIRMED").all()
            if tickets:
                t = tickets[0]
                t.status = "CANCELLED"
                ev = db.query(Event).filter(Event.id == t.event_id).first()
                if ev:
                    ev.available_tickets += 1
                db.commit()
                reply = f"Your ticket **{t.ticket_number}** for *{ev.title if ev else 'Event'}* has been cancelled and a full refund of ₹{t.price_paid:.2f} initiated."
                quick_replies = [{"label": "Explore Events", "text": "Show live upcoming events"}]
            else:
                reply = "You have no active confirmed tickets eligible for cancellation."

        elif intent == "create_event":
            from app.ml.slot_extractor import extract_event_slots
            slots = extract_event_slots(message)

            is_confirm = any(k in msg_lower for k in ["publish", "confirm", "yes", "go live", "approve"])

            if is_confirm:
                title = slots.get("title") or slots.get("event_name") or "CodeFest 2026 Hackathon"
                location = slots.get("location") or "Main Auditorium, Tech Park"
                date_str = slots.get("date") or "Sat, 24 Oct 2026"
                price = float(slots.get("price") or 299.0)
                capacity = int(slots.get("capacity") or 100)
                category = slots.get("category") or "Tech"

                ev = Event(
                    title=title,
                    description=f"Official {title} organized via ChatAssist AI Copilot.",
                    category=category,
                    location=location,
                    date_str=date_str,
                    price=price,
                    total_capacity=capacity,
                    available_tickets=capacity,
                    organizer_id=1,
                    status="PUBLISHED",
                    image_url="https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=800&auto=format&fit=crop&q=80",
                    tags=[category, "ChatCreated"]
                )
                db.add(ev)
                db.commit()
                db.refresh(ev)

                card_type = "event_card"
                card_payload = {
                    "id": ev.id,
                    "title": ev.title,
                    "category": ev.category,
                    "date_str": ev.date_str,
                    "location": ev.location,
                    "price": ev.price,
                    "available_tickets": ev.available_tickets,
                    "image_url": ev.image_url
                }

                reply = f"🎉 **{ev.title}** is now published live on ChatAssist! It is immediately active on Explore Events and open for attendee bookings."
                quick_replies = [
                    {"label": f"Book Ticket (₹{int(ev.price)})", "text": f"Book ticket for {ev.title}"},
                    {"label": "Explore All Events", "text": "Show live upcoming events"}
                ]
            else:
                event_title_draft = slots['title'] or 'CodeFest 2026 Hackathon'
                reply = (
                    f"I would be glad to help you create your event!\n\n"
                    f"📋 **Draft Event Summary**:\n"
                    f"• Title: {event_title_draft}\n"
                    f"• Date: {slots['date']}\n"
                    f"• Location: {slots['location']}\n"
                    f"• Ticket Price: ₹{slots['price']:.0f}\n"
                    f"• Maximum Capacity: {slots['capacity']} seats\n\n"
                    f"Tap **🚀 Publish Event Live** below to publish it live on ChatAssist:"
                )
                quick_replies = [
                    {"label": "🚀 Publish Event Live", "text": f"Publish event {event_title_draft}"},
                    {"label": "❌ Cancel Draft", "text": "Cancel event creation"}
                ]

        else:
            # Fallback for General Chat / LLM Reasoning
            grounding_status = "LLM_REASONED"
            reply = self._call_llm_fallback(message, db)
            quick_replies = [
                {"label": "Explore Events", "text": "Show live upcoming events"},
                {"label": "My Tickets", "text": "Show my tickets"}
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

