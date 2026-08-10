from enum import Enum
import uuid
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.ticket import Event, Ticket
from app.models.payment import Payment
from app.ml.slot_extractor import extract_event_slots

class BookingState(str, Enum):
    IDLE = "IDLE"
    EVENT_SELECTED = "EVENT_SELECTED"
    QTY_SELECTED = "QTY_SELECTED"
    PAYMENT_PENDING = "PAYMENT_PENDING"
    PAID = "PAID"

class BookingSession:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.state = BookingState.IDLE
        self.event_id: Optional[int] = None
        self.ticket_type: str = "Standard"
        self.quantity: int = 1
        self.unit_price: float = 0.0
        self.booking_id: Optional[int] = None
        self.order_id: Optional[str] = None

    def reset(self):
        self.state = BookingState.IDLE
        self.event_id = None
        self.ticket_type = "Standard"
        self.quantity = 1
        self.unit_price = 0.0
        self.booking_id = None
        self.order_id = None

# Global in-memory user sessions
booking_sessions: Dict[int, BookingSession] = {}

def get_booking_session(user_id: int) -> BookingSession:
    if user_id not in booking_sessions:
        booking_sessions[user_id] = BookingSession(user_id)
    return booking_sessions[user_id]

def handle_book_ticket_turn(user_id: int, message: str, slots: Dict[str, Any], db: Session) -> Dict[str, Any]:
    session = get_booking_session(user_id)
    msg_lower = message.lower()

    # Allow user to reset flow
    if any(k in msg_lower for k in ["cancel", "reset", "start over", "abort", "different event"]):
        session.reset()
        return {
            "reply": "Booking flow cancelled. How else can I assist you with events today?",
            "intent": "book_ticket",
            "confidence": 0.98,
            "routed_to": "BOOKING_STATE_MACHINE",
            "grounding_status": "GROUNDED_LIVE_DB",
            "type": "text",
            "payload": None,
            "quick_replies": [
                {"label": "Explore Events", "text": "Show live upcoming events"},
                {"label": "My Tickets", "text": "Show my tickets"}
            ]
        }

    # Auto-reset session if user initiates a new booking request while in PAYMENT_PENDING or PAID state
    if session.state in [BookingState.PAYMENT_PENDING, BookingState.PAID] or any(k in msg_lower for k in ["book", "buy", "reserve"]):
        if any(k in msg_lower for k in ["book", "buy", "reserve"]) and session.state != BookingState.EVENT_SELECTED and session.state != BookingState.QTY_SELECTED:
            session.reset()

    # State Machine Handling

    # State 1: IDLE or matching fresh event lookup
    if session.state == BookingState.IDLE:
        event = None
        extracted_name = slots.get("event_name") or slots.get("title")
        
        if extracted_name:
            # Fuzzy match in DB
            events = db.query(Event).filter(Event.title.ilike(f"%{extracted_name}%")).all()
            if events:
                event = events[0]

        if not event:
            # Default to first available published event
            event = db.query(Event).filter(Event.available_tickets > 0).first()

        if not event:
            return {
                "reply": "Sorry, there are no live events available right now.",
                "intent": "book_ticket",
                "confidence": 0.95,
                "routed_to": "BOOKING_STATE_MACHINE",
                "grounding_status": "GROUNDED_LIVE_DB",
                "type": "text",
                "payload": None
            }

        session.event_id = event.id
        session.state = BookingState.EVENT_SELECTED
        session.unit_price = event.price

        # Fast path: If quantity or tier were already specified in the user's initial message, advance to QTY_SELECTED directly
        if slots.get("quantity") or "vip" in msg_lower or "standard" in msg_lower:
            return handle_book_ticket_turn(user_id, message, slots, db)

        event_payload = {
            "id": event.id,
            "title": event.title,
            "category": event.category,
            "date_str": event.date_str,
            "location": event.location,
            "price": event.price,
            "available_tickets": event.available_tickets,
            "image_url": event.image_url,
            "ticket_types": event.ticket_types or [
                {"name": "Standard", "price": event.price},
                {"name": "VIP Pass", "price": round(event.price * 1.5, 0)}
            ]
        }

        return {
            "reply": f"Here is **{event.title}**! Live DB ticket price is ₹{event.price:.0f} ({event.available_tickets} seats remaining). How many tickets and which tier would you like?",
            "intent": "book_ticket",
            "confidence": 0.99,
            "routed_to": "BOOKING_STATE_MACHINE",
            "grounding_status": "GROUNDED_LIVE_DB",
            "type": "event_card",
            "payload": event_payload,
            "quick_replies": [
                {"label": "1 Standard (₹" + str(int(event.price)) + ")", "text": "1 Standard ticket"},
                {"label": "2 Standard", "text": "2 Standard tickets"},
                {"label": "2 VIP Pass", "text": "2 VIP Pass tickets"}
            ]
        }

    # State 2: EVENT_SELECTED -> user specifies quantity and ticket tier
    if session.state == BookingState.EVENT_SELECTED:
        event = db.query(Event).filter(Event.id == session.event_id).first()
        if not event:
            session.reset()
            return handle_book_ticket_turn(user_id, message, slots, db)

        # Extract quantity and ticket tier
        qty = slots.get("quantity") or 1
        if not isinstance(qty, int) or qty < 1:
            qty = 1
        
        ticket_type = slots.get("ticket_type", "Standard")
        if "vip" in msg_lower:
            ticket_type = "VIP Pass"

        # Calculate live price from DB grounding
        unit_price = event.price
        if ticket_type.lower().startswith("vip"):
            unit_price = round(event.price * 1.5, 0)

        subtotal = unit_price * qty
        gst_tax = round(subtotal * 0.18, 2)
        total = subtotal + gst_tax

        session.quantity = qty
        session.ticket_type = ticket_type
        session.unit_price = unit_price
        session.state = BookingState.QTY_SELECTED

        summary_payload = {
            "event_id": event.id,
            "event_title": event.title,
            "location": event.location,
            "date_str": event.date_str,
            "ticket_type": ticket_type,
            "quantity": qty,
            "unit_price": unit_price,
            "subtotal": subtotal,
            "tax": gst_tax,
            "total": total,
            "available_tickets": event.available_tickets
        }

        return {
            "reply": f"Here is your booking breakdown for **{event.title}** ({qty} x {ticket_type}):\n• Subtotal: ₹{subtotal:.0f}\n• GST (18%): ₹{gst_tax:.0f}\n• **Total: ₹{total:.0f}**\n\nWould you like to confirm and proceed to secure checkout?",
            "intent": "book_ticket",
            "confidence": 0.99,
            "routed_to": "BOOKING_STATE_MACHINE",
            "grounding_status": "GROUNDED_LIVE_DB",
            "type": "booking_summary",
            "payload": summary_payload,
            "quick_replies": [
                {"label": f"✅ Confirm & Pay ₹{int(total)}", "text": "Confirm booking"},
                {"label": "❌ Start Over", "text": "Cancel booking"}
            ]
        }

    # State 3: QTY_SELECTED -> user confirms booking
    if session.state == BookingState.QTY_SELECTED:
        event = db.query(Event).filter(Event.id == session.event_id).first()
        if not event:
            session.reset()
            return handle_book_ticket_turn(user_id, message, slots, db)

        if any(k in msg_lower for k in ["confirm", "yes", "pay", "proceed", "sure", "ok"]):
            subtotal = session.unit_price * session.quantity
            gst_tax = round(subtotal * 0.18, 2)
            total = subtotal + gst_tax

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
                "quantity": session.quantity,
                "unit_price": session.unit_price,
                "subtotal": subtotal,
                "tax": gst_tax,
                "amount": int(total * 100), # in paise for Razorpay standard
                "total_inr": total
            }

            return {
                "reply": f"Awesome! Click **Pay ₹{total:.0f} Securely** below to complete your booking inside the chat.",
                "intent": "book_ticket",
                "confidence": 0.99,
                "routed_to": "BOOKING_STATE_MACHINE",
                "grounding_status": "GROUNDED_LIVE_DB",
                "type": "payment_button",
                "payload": payment_payload,
                "quick_replies": None
            }

    # Fallback if in PAYMENT_PENDING or other state
    event = db.query(Event).filter(Event.id == session.event_id).first() if session.event_id else None
    return {
        "reply": "Please tap the payment button above to complete your order, or type 'cancel' to start over.",
        "intent": "book_ticket",
        "confidence": 0.90,
        "routed_to": "BOOKING_STATE_MACHINE",
        "grounding_status": "GROUNDED_LIVE_DB",
        "type": "text",
        "payload": None
    }
