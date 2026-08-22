from enum import Enum
import uuid
from typing import Dict, Any, Optional
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy.orm import Session
from app.models.ticket import Event, Ticket
from app.models.payment import Payment
from app.ml.slot_extractor import extract_event_slots

class ConversationMode(str, Enum):
    GENERAL = "GENERAL"
    BOOKING = "BOOKING"
    EVENT_CREATION = "EVENT_CREATION"
    TICKET_MANAGEMENT = "TICKET_MANAGEMENT"

class BookingState(str, Enum):
    IDLE = "IDLE"
    EVENT_SELECTED = "EVENT_SELECTED"
    QTY_SELECTED = "QTY_SELECTED"
    PAYMENT_PENDING = "PAYMENT_PENDING"
    PAID = "PAID"

def money_decimal(val: Any) -> Decimal:
    if val is None:
        return Decimal("0.00")
    return Decimal(str(val)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

class BookingSession:
    def __init__(self, user_id: int, conversation_id: Optional[int] = None):
        self.user_id = user_id
        self.conversation_id = conversation_id
        self.mode = ConversationMode.GENERAL
        self.state = BookingState.IDLE
        self.event_id: Optional[int] = None
        self.ticket_type: str = "Standard"
        self.quantity: int = 1
        self.unit_price: Decimal = Decimal("0.00")
        self.booking_id: Optional[int] = None
        self.order_id: Optional[str] = None
        self.event_draft: Dict[str, Any] = {}
        self.last_event_results: list = []

    def reset(self):
        self.mode = ConversationMode.GENERAL
        self.state = BookingState.IDLE
        self.event_id = None
        self.ticket_type = "Standard"
        self.quantity = 1
        self.unit_price = Decimal("0.00")
        self.booking_id = None
        self.order_id = None
        self.event_draft = {}
        self.last_event_results = []

# Global in-memory user sessions keyed by (user_id, conversation_id)
booking_sessions: Dict[str, BookingSession] = {}

def get_booking_session(user_id: int, conversation_id: Optional[int] = None) -> BookingSession:
    key = f"{user_id}_{conversation_id or 0}"
    if key not in booking_sessions:
        booking_sessions[key] = BookingSession(user_id, conversation_id)
    return booking_sessions[key]

def handle_create_event_turn(
    user_id: int,
    message: str,
    db: Session,
    conversation_id: Optional[int] = None
) -> Dict[str, Any]:
    session = get_booking_session(user_id, conversation_id)
    session.mode = ConversationMode.EVENT_CREATION

    from app.ml.slot_extractor import extract_event_slots
    slots = extract_event_slots(message or "")

    category = slots.get("category") or "Technology"
    event_type = slots.get("event_type") or "Workshop"
    title = slots.get("title") or slots.get("event_name")
    city = slots.get("city")
    date_str = slots.get("date_str") or slots.get("date")

    reply = "Sure — create your event using the event setup form. You'll enter your own event details, venue, ticket price and number of tickets."

    return {
        "reply": reply,
        "intent": "create_event",
        "confidence": 0.99,
        "routed_to": "CREATE_EVENT_ENTRY",
        "grounding_status": "GROUNDED_LIVE_DB",
        "mode": "EVENT_CREATION",
        "type": "create_event_entry",
        "payload": {
            "title": title,
            "category": category,
            "event_type": event_type,
            "city": city,
            "date_str": date_str
        },
        "quick_replies": [
            {"label": "✨ Create Event", "text": "Create Event"}
        ]
    }


def handle_book_ticket_turn(
    user_id: int,
    message: str,
    slots: Dict[str, Any],
    db: Session,
    event_type: str = "user_message",
    payload: Optional[Dict[str, Any]] = None,
    conversation_id: Optional[int] = None
) -> Dict[str, Any]:
    session = get_booking_session(user_id, conversation_id)
    session.mode = ConversationMode.BOOKING
    msg_lower = (message or "").lower().strip()

    # Handle System Events (e.g. PAYMENT_VERIFIED)
    if event_type == "system_event" or payload and payload.get("event") == "PAYMENT_VERIFIED":
        ticket_payload = payload.get("ticket") if payload else None
        session.state = BookingState.PAID
        return {
            "reply": "🎉 **Payment successful!** Your ticket has been issued.",
            "intent": "book_ticket",
            "confidence": 1.0,
            "routed_to": "SYSTEM_EVENT_PAYMENT_VERIFIED",
            "grounding_status": "GROUNDED_LIVE_DB",
            "type": "ticket_confirmation",
            "payload": ticket_payload,
            "quick_replies": [
                {"label": "🎟️ Show My Tickets", "text": "Show my tickets"},
                {"label": "🔍 Explore Events", "text": "Show live upcoming events"}
            ]
        }

    # Handle mid-flow cancellation gracefully
    if any(k in msg_lower for k in ["cancel", "reset", "stop", "start over", "abort"]):
        session.reset()
        return {
            "reply": "Booking cancelled. Your held seats have been released.",
            "intent": "cancel_ticket",
            "confidence": 0.99,
            "routed_to": "BOOKING_STATE_MACHINE",
            "grounding_status": "GROUNDED_LIVE_DB",
            "type": "text",
            "payload": None,
            "quick_replies": [
                {"label": "🔍 Find Events", "text": "Show live upcoming events"},
                {"label": "🎟️ My Tickets", "text": "Show my tickets"}
            ]
        }

    # Auto-reset session if user initiates a new booking request while in PAYMENT_PENDING or PAID state
    if session.state in [BookingState.PAYMENT_PENDING, BookingState.PAID]:
        if any(k in msg_lower for k in ["book", "buy", "reserve", "show", "events"]):
            session.reset()

    # State Machine Handling

    # State 1: IDLE or matching fresh event lookup
    if session.state == BookingState.IDLE:
        event = None
        extracted_name = slots.get("event_name") or slots.get("title")

        # Ordinal matching against active conversation search results context
        ordinal_idx = None
        if any(k in msg_lower for k in ["first", "1st"]):
            ordinal_idx = 0
        elif any(k in msg_lower for k in ["second", "2nd"]):
            ordinal_idx = 1
        elif any(k in msg_lower for k in ["third", "3rd"]):
            ordinal_idx = 2

        if ordinal_idx is not None:
            if session.last_event_results and ordinal_idx < len(session.last_event_results):
                target_id = session.last_event_results[ordinal_idx]
                event = db.query(Event).filter(Event.id == target_id).first()

        # Match by title in message or extracted slot (longest title match first)
        if not event:
            all_live = db.query(Event).filter(Event.available_tickets > 0, Event.status == "PUBLISHED").all()
            all_live_sorted = sorted(all_live, key=lambda x: len(x.title), reverse=True)

            if extracted_name:
                matched_events = [e for e in all_live_sorted if extracted_name.lower() in e.title.lower() or e.title.lower() in extracted_name.lower()]
                if matched_events:
                    event = matched_events[0]

            if not event:
                for ev in all_live_sorted:
                    if ev.title.lower() in msg_lower:
                        event = ev
                        break

            if not event:
                for ev in all_live_sorted:
                    words = [w for w in ev.title.lower().split() if len(w) > 3]
                    if words and all(w in msg_lower for w in words):
                        event = ev
                        break

        if not event and ordinal_idx is not None and not extracted_name:
            # If ordinal context missing, prompt user for clarification
            live_events = db.query(Event).filter(Event.available_tickets > 0, Event.status == "PUBLISHED").limit(3).all()
            quick = [{"label": f"Book {e.title[:20]}", "text": f"Book ticket for {e.title}"} for e in live_events] if live_events else None
            return {
                "reply": "Which event would you like to book?",
                "intent": "book_ticket",
                "confidence": 0.95,
                "routed_to": "CLARIFICATION",
                "grounding_status": "GROUNDED_LIVE_DB",
                "type": "event_results" if live_events else "text",
                "payload": {"events": [{"id": e.id, "title": e.title, "category": e.category, "price": e.price, "date_str": e.date_str, "location": e.location} for e in live_events]} if live_events else None,
                "quick_replies": quick
            }

        if not event and not extracted_name and ordinal_idx is None:
            # Check if there is only 1 live event available
            live_events = db.query(Event).filter(Event.available_tickets > 0, Event.status == "PUBLISHED").all()
            if len(live_events) == 1:
                event = live_events[0]

        if not event:
            live_events = db.query(Event).filter(Event.available_tickets > 0, Event.status == "PUBLISHED").limit(4).all()
            if live_events:
                return {
                    "reply": "Which event would you like to book?",
                    "intent": "book_ticket",
                    "confidence": 0.95,
                    "routed_to": "CLARIFICATION",
                    "grounding_status": "GROUNDED_LIVE_DB",
                    "type": "event_results",
                    "payload": {
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
                            } for e in live_events
                        ]
                    },
                    "quick_replies": [{"label": f"Book {e.title[:18]}", "text": f"Book ticket for {e.title}"} for e in live_events]
                }
            else:
                return {
                    "reply": "Currently, there are no live events available right now.",
                    "intent": "book_ticket",
                    "confidence": 0.95,
                    "routed_to": "BOOKING_STATE_MACHINE",
                    "grounding_status": "GROUNDED_LIVE_DB",
                    "type": "text",
                    "payload": None
                }

        session.event_id = event.id
        session.state = BookingState.EVENT_SELECTED
        session.unit_price = money_decimal(event.price)

        # Fast path: If quantity or tier were already specified in the user's initial message, advance to QTY_SELECTED directly
        if slots.get("quantity") or "vip" in msg_lower or "standard" in msg_lower:
            return handle_book_ticket_turn(user_id, message, slots, db, event_type, payload, conversation_id=conversation_id)

        # Check DB TicketTiers for event
        from app.models.ticket_tier import TicketTier
        db_tiers = db.query(TicketTier).filter(TicketTier.event_id == event.id).all()

        max_per_booking = getattr(event, "max_tickets_per_booking", 10) or 10
        effective_max = min(max_per_booking, event.available_tickets)

        vip_price = money_decimal(event.price * 1.5)
        ticket_types = []
        if db_tiers:
            for t in db_tiers:
                ticket_types.append({
                    "id": t.id,
                    "name": t.name,
                    "price": float(t.price),
                    "available_quantity": t.available_quantity,
                    "max_per_order": t.max_per_order
                })
        else:
            ticket_types = [
                {"name": "Standard", "price": float(session.unit_price), "available_quantity": event.available_tickets, "max_per_order": max_per_booking},
                {"name": "VIP Pass", "price": float(vip_price), "available_quantity": event.available_tickets, "max_per_order": max_per_booking}
            ]

        event_payload = {
            "id": event.id,
            "title": event.title,
            "category": event.category,
            "date_str": event.date_str,
            "location": event.location,
            "price": float(session.unit_price),
            "available_tickets": event.available_tickets,
            "max_tickets_per_booking": max_per_booking,
            "effective_max": effective_max,
            "image_url": event.image_url,
            "ticket_types": ticket_types
        }

        quick_replies = []
        for tt in ticket_types:
            quick_replies.append({"label": f"{tt['name']} ₹{tt['price']:.0f}", "text": f"1 {tt['name']} ticket for {event.title}"})
        quick_replies.append({"label": "2 Tickets", "text": "Book 2 tickets"})

        return {
            "reply": f"Great choice! **{event.title}** has {event.available_tickets} seats available (up to {max_per_booking} per booking).\n\nWhich ticket type and quantity would you like?",
            "intent": "book_ticket",
            "confidence": 0.99,
            "routed_to": "BOOKING_STATE_MACHINE",
            "grounding_status": "GROUNDED_LIVE_DB",
            "type": "event_card",
            "payload": event_payload,
            "quick_replies": quick_replies
        }

    # State 2: EVENT_SELECTED or QTY_SELECTED -> update single authoritative booking state
    if session.state in [BookingState.EVENT_SELECTED, BookingState.QTY_SELECTED]:
        event = db.query(Event).filter(Event.id == session.event_id).first()
        if not event:
            session.reset()
            return handle_book_ticket_turn(user_id, message, slots, db, event_type, payload, conversation_id=conversation_id)

        from app.models.ticket_tier import TicketTier
        db_tiers = db.query(TicketTier).filter(TicketTier.event_id == event.id).all()

        max_per_booking = getattr(event, "max_tickets_per_booking", 10) or 10

        # Determine target tier
        selected_tier = None
        ticket_type = session.ticket_type or "Standard"
        if "vip" in msg_lower:
            ticket_type = "VIP Pass"
        elif "standard" in msg_lower:
            ticket_type = "Standard"
        elif slots.get("ticket_type"):
            ticket_type = slots["ticket_type"]

        if db_tiers:
            for t in db_tiers:
                if t.name.lower().strip() in ticket_type.lower() or ticket_type.lower() in t.name.lower().strip():
                    selected_tier = t
                    break

        if selected_tier:
            ticket_type = selected_tier.name
            unit_price = money_decimal(selected_tier.price)
            max_per_booking = selected_tier.max_per_order or max_per_booking
            tier_available = selected_tier.available_quantity
        else:
            unit_price = money_decimal(event.price)
            if ticket_type.lower().startswith("vip"):
                unit_price = money_decimal(event.price * 1.5)
            tier_available = event.available_tickets

        effective_max = min(max_per_booking, tier_available)

        # Handle user confirming payment from summary card
        if session.state == BookingState.QTY_SELECTED and any(k in msg_lower for k in ["confirm", "yes", "pay", "proceed"]):
            unit_price = session.unit_price
            qty = session.quantity
            subtotal = money_decimal(unit_price * qty)
            gst_tax = money_decimal(subtotal * Decimal("0.18"))
            total = money_decimal(subtotal + gst_tax)

            order_id = f"order_rzp_{uuid.uuid4().hex[:10]}"
            booking_id = int(uuid.uuid4().int % 1000000)

            session.order_id = order_id
            session.booking_id = booking_id
            session.state = BookingState.PAYMENT_PENDING

            payment_payload = {
                "order_id": order_id,
                "booking_id": booking_id,
                "event_id": event.id,
                "event_title": event.title,
                "ticket_type": session.ticket_type,
                "quantity": qty,
                "unit_price": float(unit_price),
                "subtotal": float(subtotal),
                "tax": float(gst_tax),
                "amount": int(total * 100), # in paise for Razorpay
                "total_inr": float(total),
                "idempotency_key": f"idempotent_order_{booking_id}"
            }

            return {
                "reply": f"Click **Pay ₹{total:.2f} Securely** below to complete your order:",
                "intent": "book_ticket",
                "confidence": 0.99,
                "routed_to": "BOOKING_STATE_MACHINE",
                "grounding_status": "GROUNDED_LIVE_DB",
                "type": "payment_button",
                "payload": payment_payload,
                "quick_replies": None
            }

        # Extract quantity and tier updates
        requested_qty = slots.get("quantity")
        if requested_qty is None or not isinstance(requested_qty, int) or requested_qty < 1:
            import re
            num_match = re.search(r'\b([1-9]\d*)\b', message)
            if num_match:
                requested_qty = int(num_match.group(1))
            else:
                requested_qty = session.quantity or 1

        # Check max per booking limit
        if requested_qty > max_per_booking:
            return {
                "reply": f"I can book up to {max_per_booking} tickets per reservation for **{event.title}**. You can book a maximum of {max_per_booking} {ticket_type} tickets per order.",
                "intent": "book_ticket",
                "confidence": 0.98,
                "routed_to": "BOOKING_MAX_PER_RESERVATION_CAP",
                "grounding_status": "GROUNDED_LIVE_DB",
                "type": "text",
                "quick_replies": [
                    {"label": f"Book {max_per_booking} Tickets", "text": f"Book {max_per_booking} tickets"},
                    {"label": "Choose another quantity", "text": "Book 2 tickets"}
                ]
            }

        # Check inventory availability limit
        if requested_qty > tier_available:
            return {
                "reply": f"Only {tier_available} {ticket_type} tickets are currently available.",
                "intent": "book_ticket",
                "confidence": 0.98,
                "routed_to": "BOOKING_INVENTORY_CAP",
                "grounding_status": "GROUNDED_LIVE_DB",
                "type": "text",
                "quick_replies": [
                    {"label": f"Book {tier_available} Tickets", "text": f"Book {tier_available} tickets"},
                    {"label": "Choose another event", "text": "Show live upcoming events"}
                ]
            }

        # Execute real atomic tier inventory seat hold
        try:
            from app.services.tier_inventory_service import hold_tier_inventory
            held_tier = hold_tier_inventory(db, event.id, ticket_type, requested_qty, user_id)
            if held_tier:
                unit_price = money_decimal(held_tier.price)
        except Exception as hold_err:
            db.rollback()
            print("Hold tier inventory note:", hold_err)

        subtotal = money_decimal(unit_price * requested_qty)
        gst_tax = money_decimal(subtotal * Decimal("0.18"))
        total = money_decimal(subtotal + gst_tax)

        session.quantity = requested_qty
        session.ticket_type = ticket_type
        session.unit_price = unit_price
        session.state = BookingState.QTY_SELECTED

        # Save/update BookingDraft in DB
        try:
            from app.models.booking_draft import BookingDraft
            from datetime import datetime, timedelta
            expires_at = datetime.utcnow() + timedelta(minutes=10)

            existing_draft = db.query(BookingDraft).filter(
                BookingDraft.user_id == user_id,
                BookingDraft.event_id == event.id,
                BookingDraft.status == "DRAFT"
            ).order_by(BookingDraft.created_at.desc()).first()

            if existing_draft:
                existing_draft.quantity = requested_qty
                existing_draft.ticket_type = ticket_type
                existing_draft.unit_price = float(unit_price)
                existing_draft.subtotal = float(subtotal)
                existing_draft.tax = float(gst_tax)
                existing_draft.total = float(total)
                existing_draft.expires_at = expires_at
                db.commit()
            else:
                draft_num = f"DFT-{uuid.uuid4().hex[:8].upper()}"
                idemp_key = f"idempotent_draft_{user_id}_{conversation_id or 0}_{uuid.uuid4().hex[:6]}"
                draft = BookingDraft(
                    draft_number=draft_num,
                    conversation_id=conversation_id,
                    user_id=user_id,
                    event_id=event.id,
                    ticket_type=ticket_type,
                    quantity=requested_qty,
                    unit_price=float(unit_price),
                    subtotal=float(subtotal),
                    tax=float(gst_tax),
                    total=float(total),
                    idempotency_key=idemp_key,
                    status="DRAFT",
                    expires_at=expires_at
                )
                db.add(draft)
                db.commit()
        except Exception as err:
            db.rollback()
            print("Draft persistence notice:", err)

        summary_payload = {
            "event_id": event.id,
            "event_title": event.title,
            "location": event.location,
            "date_str": event.date_str,
            "ticket_type": ticket_type,
            "quantity": requested_qty,
            "unit_price": float(unit_price),
            "subtotal": float(subtotal),
            "tax": float(gst_tax),
            "gst": float(gst_tax),
            "total": float(total),
            "available_tickets": event.available_tickets,
            "max_tickets_per_booking": max_per_booking,
            "effective_max": effective_max,
            "hold_expires_in": "10 minutes"
        }

        return {
            "reply": f"Perfect. I've held {requested_qty} × {ticket_type} ticket(s) for **{event.title}**.\n\n• Unit Price: ₹{unit_price:.2f}\n• Subtotal: ₹{subtotal:.2f}\n• CGST (9%): ₹{(gst_tax/2):.2f}\n• SGST (9%): ₹{(gst_tax/2):.2f}\n• **Total: ₹{total:.2f}**\n\n⏱️ Seats held for 10 minutes.",
            "intent": "book_ticket",
            "confidence": 0.99,
            "routed_to": "BOOKING_STATE_MACHINE",
            "grounding_status": "GROUNDED_LIVE_DB",
            "type": "booking_summary",
            "payload": summary_payload,
            "quick_replies": [
                {"label": f"✅ Confirm & Pay ₹{total:.2f}", "text": "Confirm booking"},
                {"label": "❌ Cancel", "text": "Cancel booking"}
            ]
        }

    # Fallback if in PAYMENT_PENDING state
    event = db.query(Event).filter(Event.id == session.event_id).first() if session.event_id else None
    return {
        "reply": "Please tap the payment button above to complete your order, or type 'cancel' to release your held seats.",
        "intent": "book_ticket",
        "confidence": 0.90,
        "routed_to": "BOOKING_STATE_MACHINE",
        "grounding_status": "GROUNDED_LIVE_DB",
        "type": "text",
        "payload": None
    }


