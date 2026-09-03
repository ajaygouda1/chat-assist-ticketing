import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.models.ticket import Event, Ticket
from app.models.ticket_tier import TicketTier
from app.models.booking_draft import BookingDraft
from app.models.payment import Payment
from app.models.waitlist import WaitlistEntry
from app.models.refund import RefundPolicy, RefundRequest
from app.models.ticket_transfer import TicketTransfer
from app.services.tier_inventory_service import (
    hold_tier_inventory,
    release_tier_inventory_hold,
    confirm_tier_inventory_payment
)
from app.services.promo_service import validate_and_apply_promo
from app.services.qr_service import generate_ticket_qr_base64
from app.services.refund_service import calculate_refund_amount
from app.services.transfer_service import initiate_ticket_transfer
from app.services.waitlist_service import join_waitlist as svc_join_waitlist
from app.ai.schemas import ToolResult

# ---------------------------------------------------------
# Tool Implementations
# ---------------------------------------------------------

def tool_search_events(
    db: Session,
    query: Optional[str] = None,
    category: Optional[str] = None,
    city: Optional[str] = None,
    max_price: Optional[float] = None,
    date_filter: Optional[str] = None
) -> ToolResult:
    try:
        q = db.query(Event).filter(Event.available_tickets > 0, Event.status == "PUBLISHED")

        if query and query.strip():
            kw = query.strip()
            q = q.filter(
                or_(
                    Event.title.ilike(f"%{kw}%"),
                    Event.description.ilike(f"%{kw}%"),
                    Event.category.ilike(f"%{kw}%"),
                    Event.location.ilike(f"%{kw}%")
                )
            )

        if category and category.strip():
            cat = category.strip()
            if cat.lower() in ["tech", "technology"]:
                q = q.filter(or_(Event.category.ilike("%Tech%"), Event.category.ilike("%Technology%")))
            elif cat.lower() in ["ai", "artificial intelligence"]:
                q = q.filter(or_(Event.category.ilike("%AI%"), Event.title.ilike("%AI%")))
            else:
                q = q.filter(Event.category.ilike(f"%{cat}%"))

        if city and city.strip():
            c = city.strip()
            if "beng" in c.lower() or "bang" in c.lower():
                q = q.filter(Event.location.ilike("%Bengaluru%"))
            elif "mang" in c.lower():
                q = q.filter(Event.location.ilike("%Mangaluru%"))
            else:
                q = q.filter(Event.location.ilike(f"%{c}%"))

        if max_price is not None and max_price > 0:
            q = q.filter(Event.price <= max_price)

        events = q.all()

        # Fallback if filter was overly restrictive
        if not events and (category or max_price or query):
            events = db.query(Event).filter(Event.available_tickets > 0, Event.status == "PUBLISHED").limit(6).all()

        event_items = [
            {
                "id": e.id,
                "title": e.title,
                "category": e.category,
                "location": e.location,
                "venue": e.venue or e.location,
                "date_str": e.date_str,
                "price": float(e.price) if e.price else 0.0,
                "available_tickets": e.available_tickets,
                "image_url": e.image_url
            }
            for e in events[:3]
        ]

        return ToolResult(
            success=True,
            data={
                "total_found": len(event_items),
                "events": event_items
            }
        )
    except Exception as e:
        return ToolResult(success=False, error={"code": "SEARCH_FAILED", "message": str(e)})


def tool_get_event_details(db: Session, event_id: int) -> ToolResult:
    try:
        e = db.query(Event).filter(Event.id == event_id).first()
        if not e:
            return ToolResult(success=False, error={"code": "EVENT_NOT_FOUND", "message": f"Event #{event_id} not found."})

        tiers = db.query(TicketTier).filter(TicketTier.event_id == e.id).all()
        tier_list = [
            {
                "id": t.id,
                "name": t.name,
                "price": float(t.price),
                "available_quantity": t.available_quantity,
                "min_per_order": t.min_per_order,
                "max_per_order": t.max_per_order
            }
            for t in tiers
        ]

        return ToolResult(
            success=True,
            data={
                "id": e.id,
                "title": e.title,
                "category": e.category,
                "description": e.description,
                "location": e.location,
                "venue": e.venue or e.location,
                "address": e.address,
                "date_str": e.date_str,
                "start_time": e.start_time or "10:00 AM",
                "end_time": e.end_time or "05:00 PM",
                "price": float(e.price) if e.price else 0.0,
                "available_tickets": e.available_tickets,
                "max_tickets_per_booking": getattr(e, "max_tickets_per_booking", 10) or 10,
                "cancellation_policy": e.cancellation_policy or "Flexible",
                "image_url": e.image_url,
                "tiers": tier_list
            }
        )
    except Exception as e:
        return ToolResult(success=False, error={"code": "DETAILS_FAILED", "message": str(e)})


def tool_get_event_tiers(db: Session, event_id: int) -> ToolResult:
    try:
        e = db.query(Event).filter(Event.id == event_id).first()
        if not e:
            return ToolResult(success=False, error={"code": "EVENT_NOT_FOUND", "message": f"Event #{event_id} not found."})

        tiers = db.query(TicketTier).filter(TicketTier.event_id == event_id).all()
        if not tiers:
            tier_list = [
                {"id": 1, "name": "Standard", "price": float(e.price), "available_quantity": e.available_tickets, "min_per_order": 1, "max_per_order": 10},
                {"id": 2, "name": "VIP Pass", "price": float(e.price * 1.5), "available_quantity": e.available_tickets, "min_per_order": 1, "max_per_order": 10}
            ]
        else:
            tier_list = [
                {
                    "id": t.id,
                    "name": t.name,
                    "price": float(t.price),
                    "available_quantity": t.available_quantity,
                    "min_per_order": t.min_per_order,
                    "max_per_order": t.max_per_order
                }
                for t in tiers
            ]

        return ToolResult(
            success=True,
            data={
                "event_id": event_id,
                "event_title": e.title,
                "tiers": tier_list
            }
        )
    except Exception as e:
        return ToolResult(success=False, error={"code": "TIERS_FAILED", "message": str(e)})


def tool_check_ticket_availability(db: Session, event_id: int, tier_name: Optional[str] = None) -> ToolResult:
    try:
        e = db.query(Event).filter(Event.id == event_id).first()
        if not e:
            return ToolResult(success=False, error={"code": "EVENT_NOT_FOUND", "message": f"Event #{event_id} not found."})

        if tier_name:
            tier = db.query(TicketTier).filter(
                TicketTier.event_id == event_id,
                TicketTier.name.ilike(f"%{tier_name.strip()}%")
            ).first()
            if tier:
                return ToolResult(
                    success=True,
                    data={
                        "event_id": event_id,
                        "event_title": e.title,
                        "tier_name": tier.name,
                        "available_quantity": tier.available_quantity,
                        "price": float(tier.price),
                        "is_sold_out": tier.available_quantity <= 0
                    }
                )

        return ToolResult(
            success=True,
            data={
                "event_id": event_id,
                "event_title": e.title,
                "total_available": e.available_tickets,
                "is_sold_out": e.available_tickets <= 0
            }
        )
    except Exception as e:
        return ToolResult(success=False, error={"code": "AVAILABILITY_FAILED", "message": str(e)})


def tool_calculate_booking_total(
    db: Session,
    event_id: int,
    tier_name: str = "Standard",
    quantity: int = 1,
    promo_code: Optional[str] = None,
    user_id: int = 1
) -> ToolResult:
    try:
        e = db.query(Event).filter(Event.id == event_id).first()
        if not e:
            return ToolResult(success=False, error={"code": "EVENT_NOT_FOUND", "message": f"Event #{event_id} not found."})

        tier = db.query(TicketTier).filter(
            TicketTier.event_id == event_id,
            TicketTier.name.ilike(f"%{tier_name.strip()}%")
        ).first()

        unit_price = float(tier.price) if tier else (float(e.price * 1.5) if "vip" in tier_name.lower() else float(e.price))
        subtotal = round(unit_price * quantity, 2)
        discount = 0.0

        if promo_code and promo_code.strip():
            try:
                p_res = validate_and_apply_promo(db, promo_code.strip(), user_id, event_id, subtotal)
                discount = p_res.get("discount_amount", 0.0)
            except Exception:
                discount = 0.0

        taxable = max(0.0, subtotal - discount)
        gst = round(taxable * 0.18, 2)
        cgst = round(gst / 2.0, 2)
        sgst = round(gst / 2.0, 2)
        total = round(taxable + gst, 2)

        return ToolResult(
            success=True,
            data={
                "event_id": event_id,
                "event_title": e.title,
                "tier_name": tier.name if tier else tier_name,
                "quantity": quantity,
                "unit_price": unit_price,
                "subtotal": subtotal,
                "discount": discount,
                "taxable_amount": taxable,
                "cgst": cgst,
                "sgst": sgst,
                "gst_tax": gst,
                "total": total,
                "currency": "INR"
            }
        )
    except Exception as e:
        return ToolResult(success=False, error={"code": "CALCULATION_FAILED", "message": str(e)})


def tool_create_booking_draft(
    db: Session,
    user_id: int,
    event_id: int,
    tier_name: str = "Standard",
    quantity: int = 1,
    conversation_id: Optional[int] = None
) -> ToolResult:
    try:
        e = db.query(Event).filter(Event.id == event_id).first()
        if not e:
            return ToolResult(success=False, error={"code": "EVENT_NOT_FOUND", "message": f"Event #{event_id} not found."})

        # Check max per booking limit
        max_limit = getattr(e, "max_tickets_per_booking", 10) or 10
        if quantity > max_limit:
            return ToolResult(
                success=False,
                error={
                    "code": "EXCEEDS_MAX_ORDER",
                    "message": f"You can book up to {max_limit} tickets per order for this event."
                }
            )

        # Atomic hold on tier inventory
        try:
            held_tier = hold_tier_inventory(db, event_id, tier_name, quantity, user_id)
            actual_tier_name = held_tier.name if held_tier else tier_name
            unit_price = float(held_tier.price) if held_tier else float(e.price)
        except Exception as hold_err:
            db.rollback()
            return ToolResult(
                success=False,
                error={"code": "INSUFFICIENT_INVENTORY", "message": str(hold_err)}
            )

        subtotal = round(unit_price * quantity, 2)
        gst = round(subtotal * 0.18, 2)
        total = round(subtotal + gst, 2)
        expires_at = datetime.utcnow() + timedelta(minutes=10)

        # Check existing draft for this user & event
        existing_draft = db.query(BookingDraft).filter(
            BookingDraft.user_id == user_id,
            BookingDraft.event_id == event_id,
            BookingDraft.status == "DRAFT"
        ).order_by(BookingDraft.created_at.desc()).first()

        if existing_draft:
            existing_draft.quantity = quantity
            existing_draft.ticket_type = actual_tier_name
            existing_draft.unit_price = unit_price
            existing_draft.subtotal = subtotal
            existing_draft.tax = gst
            existing_draft.total = total
            existing_draft.expires_at = expires_at
            draft = existing_draft
        else:
            draft_num = f"DFT-{uuid.uuid4().hex[:8].upper()}"
            idemp_key = f"idemp_draft_{user_id}_{conversation_id or 0}_{uuid.uuid4().hex[:6]}"
            draft = BookingDraft(
                draft_number=draft_num,
                conversation_id=conversation_id,
                user_id=user_id,
                event_id=event_id,
                ticket_type=actual_tier_name,
                quantity=quantity,
                unit_price=unit_price,
                subtotal=subtotal,
                tax=gst,
                total=total,
                idempotency_key=idemp_key,
                status="DRAFT",
                expires_at=expires_at
            )
            db.add(draft)

        db.commit()
        db.refresh(draft)

        return ToolResult(
            success=True,
            data={
                "draft_id": draft.id,
                "draft_number": draft.draft_number,
                "event_id": e.id,
                "event_title": e.title,
                "location": e.location,
                "date_str": e.date_str,
                "ticket_type": actual_tier_name,
                "quantity": quantity,
                "unit_price": unit_price,
                "subtotal": subtotal,
                "tax": gst,
                "total": total,
                "expires_at": expires_at.isoformat(),
                "hold_expires_in": "10 minutes"
            }
        )
    except Exception as e:
        db.rollback()
        return ToolResult(success=False, error={"code": "DRAFT_CREATION_FAILED", "message": str(e)})


def tool_update_booking_draft(
    db: Session,
    user_id: int,
    draft_id: Optional[int] = None,
    quantity: Optional[int] = None,
    tier_name: Optional[str] = None,
    conversation_id: Optional[int] = None
) -> ToolResult:
    try:
        q = db.query(BookingDraft).filter(BookingDraft.user_id == user_id, BookingDraft.status == "DRAFT")
        if draft_id:
            draft = q.filter(BookingDraft.id == draft_id).first()
        elif conversation_id:
            draft = q.filter(BookingDraft.conversation_id == conversation_id).order_by(BookingDraft.created_at.desc()).first()
        else:
            draft = q.order_by(BookingDraft.created_at.desc()).first()

        if not draft:
            return ToolResult(success=False, error={"code": "DRAFT_NOT_FOUND", "message": "No active booking draft found to update."})

        # Release old hold
        release_tier_inventory_hold(db, draft.event_id, draft.ticket_type, draft.quantity)

        new_qty = quantity if quantity is not None else draft.quantity
        new_tier = tier_name if tier_name is not None else draft.ticket_type

        # Re-hold with new quantity and tier
        try:
            held_tier = hold_tier_inventory(db, draft.event_id, new_tier, new_qty, user_id)
            actual_tier_name = held_tier.name if held_tier else new_tier
            unit_price = float(held_tier.price) if held_tier else draft.unit_price
        except Exception as hold_err:
            # Revert old hold
            hold_tier_inventory(db, draft.event_id, draft.ticket_type, draft.quantity, user_id)
            return ToolResult(success=False, error={"code": "INSUFFICIENT_INVENTORY", "message": str(hold_err)})

        subtotal = round(unit_price * new_qty, 2)
        gst = round(subtotal * 0.18, 2)
        total = round(subtotal + gst, 2)
        expires_at = datetime.utcnow() + timedelta(minutes=10)

        draft.quantity = new_qty
        draft.ticket_type = actual_tier_name
        draft.unit_price = unit_price
        draft.subtotal = subtotal
        draft.tax = gst
        draft.total = total
        draft.expires_at = expires_at
        db.commit()
        db.refresh(draft)

        ev = db.query(Event).filter(Event.id == draft.event_id).first()

        return ToolResult(
            success=True,
            data={
                "draft_id": draft.id,
                "draft_number": draft.draft_number,
                "event_id": draft.event_id,
                "event_title": ev.title if ev else "Event",
                "location": ev.location if ev else "",
                "date_str": ev.date_str if ev else "",
                "ticket_type": actual_tier_name,
                "quantity": new_qty,
                "unit_price": unit_price,
                "subtotal": subtotal,
                "tax": gst,
                "total": total,
                "expires_at": expires_at.isoformat(),
                "hold_expires_in": "10 minutes"
            }
        )
    except Exception as e:
        db.rollback()
        return ToolResult(success=False, error={"code": "UPDATE_FAILED", "message": str(e)})


def tool_remove_booking_item(
    db: Session,
    user_id: int,
    draft_id: Optional[int] = None,
    conversation_id: Optional[int] = None
) -> ToolResult:
    try:
        q = db.query(BookingDraft).filter(BookingDraft.user_id == user_id, BookingDraft.status == "DRAFT")
        if draft_id:
            draft = q.filter(BookingDraft.id == draft_id).first()
        elif conversation_id:
            draft = q.filter(BookingDraft.conversation_id == conversation_id).order_by(BookingDraft.created_at.desc()).first()
        else:
            draft = q.order_by(BookingDraft.created_at.desc()).first()

        if not draft:
            return ToolResult(success=False, error={"code": "DRAFT_NOT_FOUND", "message": "No active booking draft found to cancel."})

        release_tier_inventory_hold(db, draft.event_id, draft.ticket_type, draft.quantity)
        draft.status = "CANCELLED"
        db.commit()

        return ToolResult(
            success=True,
            data={
                "draft_id": draft.id,
                "status": "CANCELLED",
                "message": "Your reservation has been cancelled and held seats were released."
            }
        )
    except Exception as e:
        db.rollback()
        return ToolResult(success=False, error={"code": "CANCEL_FAILED", "message": str(e)})


def tool_apply_promo_code(
    db: Session,
    user_id: int,
    promo_code: str,
    draft_id: Optional[int] = None,
    conversation_id: Optional[int] = None
) -> ToolResult:
    try:
        q = db.query(BookingDraft).filter(BookingDraft.user_id == user_id, BookingDraft.status == "DRAFT")
        if draft_id:
            draft = q.filter(BookingDraft.id == draft_id).first()
        elif conversation_id:
            draft = q.filter(BookingDraft.conversation_id == conversation_id).order_by(BookingDraft.created_at.desc()).first()
        else:
            draft = q.order_by(BookingDraft.created_at.desc()).first()

        if not draft:
            return ToolResult(success=False, error={"code": "DRAFT_NOT_FOUND", "message": "No active booking reservation found to apply promo."})

        p_res = validate_and_apply_promo(db, promo_code.strip(), user_id, draft.event_id, draft.subtotal)
        discount = p_res["discount_amount"]
        taxable = max(0.0, draft.subtotal - discount)
        gst = round(taxable * 0.18, 2)
        total = round(taxable + gst, 2)

        draft.tax = gst
        draft.total = total
        db.commit()

        ev = db.query(Event).filter(Event.id == draft.event_id).first()

        return ToolResult(
            success=True,
            data={
                "draft_id": draft.id,
                "promo_code": promo_code.upper(),
                "discount_amount": discount,
                "subtotal": draft.subtotal,
                "tax": gst,
                "total": total,
                "event_title": ev.title if ev else "Event"
            }
        )
    except Exception as e:
        return ToolResult(success=False, error={"code": "PROMO_FAILED", "message": str(e)})


def tool_create_payment_order(
    db: Session,
    user_id: int,
    draft_id: Optional[int] = None,
    conversation_id: Optional[int] = None
) -> ToolResult:
    try:
        q = db.query(BookingDraft).filter(BookingDraft.user_id == user_id, BookingDraft.status.in_(["DRAFT", "READY_FOR_PAYMENT"]))
        if draft_id:
            draft = q.filter(BookingDraft.id == draft_id).first()
        elif conversation_id:
            draft = q.filter(BookingDraft.conversation_id == conversation_id).order_by(BookingDraft.created_at.desc()).first()
        else:
            draft = q.order_by(BookingDraft.created_at.desc()).first()

        if not draft:
            return ToolResult(success=False, error={"code": "DRAFT_NOT_FOUND", "message": "No active booking reservation ready for payment."})

        if draft.is_expired():
            return ToolResult(success=False, error={"code": "HOLD_EXPIRED", "message": "Your 10-minute seat hold expired. Please restart reservation."})

        ev = db.query(Event).filter(Event.id == draft.event_id).first()
        if not ev:
            return ToolResult(success=False, error={"code": "EVENT_NOT_FOUND", "message": "Event not found."})

        order_id = f"order_rzp_{uuid.uuid4().hex[:10]}"
        booking_id = int(uuid.uuid4().int % 1000000)
        idemp_key = draft.idempotency_key or f"idempotent_order_{draft.id}_{user_id}"

        draft.status = "READY_FOR_PAYMENT"
        db.commit()

        payment_payload = {
            "order_id": order_id,
            "booking_id": draft.id,
            "event_id": ev.id,
            "event_title": ev.title,
            "ticket_type": draft.ticket_type,
            "quantity": draft.quantity,
            "unit_price": draft.unit_price,
            "subtotal": draft.subtotal,
            "tax": draft.tax,
            "amount": int(draft.total * 100),  # in paise
            "total_inr": draft.total,
            "idempotency_key": idemp_key
        }

        return ToolResult(
            success=True,
            data={
                "order_id": order_id,
                "booking_id": draft.id,
                "payment_payload": payment_payload,
                "total": draft.total
            }
        )
    except Exception as e:
        db.rollback()
        return ToolResult(success=False, error={"code": "PAYMENT_ORDER_FAILED", "message": str(e)})


def tool_get_user_tickets(db: Session, user_id: int, limit: int = 5) -> ToolResult:
    try:
        tickets = db.query(Ticket).filter(Ticket.user_id == user_id).order_by(Ticket.created_at.desc()).limit(limit).all()
        ticket_list = []
        for t in tickets:
            ev = db.query(Event).filter(Event.id == t.event_id).first()
            p = db.query(Payment).filter(Payment.user_id == user_id).order_by(Payment.id.desc()).first()
            pay_id = p.payment_id if p else f"pay_demo_{t.id}"
            token, qr_b64 = generate_ticket_qr_base64(str(t.id), pay_id, str(t.event_id))

            ticket_list.append({
                "id": t.id,
                "ticket_number": t.ticket_number,
                "event_title": ev.title if ev else "Event",
                "price_paid": float(t.price_paid) if t.price_paid else 0.0,
                "status": t.status,
                "date_str": ev.date_str if ev else "Upcoming",
                "location": ev.location if ev else "Bengaluru",
                "qr_token": token,
                "qr_code_url": qr_b64
            })

        return ToolResult(
            success=True,
            data={
                "total_tickets": len(ticket_list),
                "tickets": ticket_list
            }
        )
    except Exception as e:
        return ToolResult(success=False, error={"code": "TICKETS_FETCH_FAILED", "message": str(e)})


def tool_cancel_booking(db: Session, user_id: int, ticket_id: int, reason: Optional[str] = None) -> ToolResult:
    try:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id, Ticket.user_id == user_id).first()
        if not ticket:
            return ToolResult(success=False, error={"code": "TICKET_NOT_FOUND", "message": f"Ticket #{ticket_id} not found."})

        if ticket.status != "CONFIRMED":
            return ToolResult(success=False, error={"code": "INVALID_STATUS", "message": f"Cannot cancel ticket with status '{ticket.status}'."})

        ev = db.query(Event).filter(Event.id == ticket.event_id).first()
        refund_amount, policy_msg = calculate_refund_amount(db, ticket, ev) if ev else (ticket.price_paid, "Standard policy")

        # Invalidate ticket
        ticket.status = "CANCELLED"

        # Restore inventory
        if ev:
            ev.available_tickets += 1
            # Also restore to first tier
            tier = db.query(TicketTier).filter(TicketTier.event_id == ev.id).first()
            if tier:
                tier.available_quantity += 1
                if tier.sold_quantity > 0:
                    tier.sold_quantity -= 1

        refund_req = RefundRequest(
            ticket_id=ticket.id,
            user_id=user_id,
            event_id=ticket.event_id,
            refund_amount=refund_amount,
            status="APPROVED",
            policy_applied=policy_msg,
            reason=reason or "Customer chat cancellation",
            inventory_restored=1
        )
        db.add(refund_req)
        db.commit()

        return ToolResult(
            success=True,
            data={
                "ticket_id": ticket.id,
                "ticket_number": ticket.ticket_number,
                "event_title": ev.title if ev else "Event",
                "status": "CANCELLED",
                "refund_amount": refund_amount,
                "policy": policy_msg,
                "message": f"Ticket {ticket.ticket_number} cancelled. Refund of ₹{refund_amount:.2f} processed."
            }
        )
    except Exception as e:
        db.rollback()
        return ToolResult(success=False, error={"code": "CANCELLATION_FAILED", "message": str(e)})


def tool_transfer_ticket(db: Session, user_id: int, ticket_id: int, recipient_email: str) -> ToolResult:
    try:
        transfer = initiate_ticket_transfer(db, ticket_id, user_id, recipient_email)
        return ToolResult(
            success=True,
            data={
                "transfer_id": transfer.id,
                "ticket_id": ticket_id,
                "recipient_email": recipient_email,
                "status": transfer.status,
                "message": f"Ticket transferred successfully to {recipient_email}."
            }
        )
    except Exception as e:
        db.rollback()
        return ToolResult(success=False, error={"code": "TRANSFER_FAILED", "message": str(e)})


def tool_join_waitlist(db: Session, user_id: int, event_id: int, tier_name: str = "Standard", quantity: int = 1) -> ToolResult:
    try:
        entry = svc_join_waitlist(db, event_id, user_id, tier_name, quantity)
        ev = db.query(Event).filter(Event.id == event_id).first()
        return ToolResult(
            success=True,
            data={
                "waitlist_id": entry.id,
                "event_id": event_id,
                "event_title": ev.title if ev else "Event",
                "position": entry.position,
                "status": entry.status,
                "message": f"You are #{entry.position} on the waitlist for {ev.title if ev else 'this event'}."
            }
        )
    except Exception as e:
        db.rollback()
        return ToolResult(success=False, error={"code": "WAITLIST_FAILED", "message": str(e)})


def tool_get_event_recommendations(db: Session, user_id: int, category: Optional[str] = None, limit: int = 4) -> ToolResult:
    try:
        q = db.query(Event).filter(Event.available_tickets > 0, Event.status == "PUBLISHED")
        if category:
            q = q.filter(Event.category.ilike(f"%{category}%"))
        events = q.limit(limit).all()
        if not events:
            events = db.query(Event).filter(Event.available_tickets > 0, Event.status == "PUBLISHED").limit(limit).all()

        return ToolResult(
            success=True,
            data={
                "recommendations": [
                    {
                        "id": e.id,
                        "title": e.title,
                        "category": e.category,
                        "location": e.location,
                        "date_str": e.date_str,
                        "price": float(e.price) if e.price else 0.0,
                        "available_tickets": e.available_tickets,
                        "image_url": e.image_url
                    }
                    for e in events
                ]
            }
        )
    except Exception as e:
        return ToolResult(success=False, error={"code": "RECOMMENDATIONS_FAILED", "message": str(e)})


def tool_compare_events(db: Session, event_id_1: int, event_id_2: int) -> ToolResult:
    try:
        e1 = db.query(Event).filter(Event.id == event_id_1).first()
        e2 = db.query(Event).filter(Event.id == event_id_2).first()
        if not e1 or not e2:
            return ToolResult(success=False, error={"code": "EVENT_NOT_FOUND", "message": "One or both events could not be found for comparison."})

        tiers1 = db.query(TicketTier).filter(TicketTier.event_id == e1.id).all()
        tiers2 = db.query(TicketTier).filter(TicketTier.event_id == e2.id).all()

        has_vip_1 = any("vip" in t.name.lower() for t in tiers1)
        has_vip_2 = any("vip" in t.name.lower() for t in tiers2)

        comparison = {
            "event_1": {
                "id": e1.id,
                "title": e1.title,
                "category": e1.category,
                "date_str": e1.date_str,
                "location": e1.location,
                "venue": e1.venue or e1.location,
                "price": float(e1.price),
                "available_tickets": e1.available_tickets,
                "vip_available": has_vip_1
            },
            "event_2": {
                "id": e2.id,
                "title": e2.title,
                "category": e2.category,
                "date_str": e2.date_str,
                "location": e2.location,
                "venue": e2.venue or e2.location,
                "price": float(e2.price),
                "available_tickets": e2.available_tickets,
                "vip_available": has_vip_2
            }
        }
        return ToolResult(success=True, data=comparison)
    except Exception as e:
        return ToolResult(success=False, error={"code": "COMPARE_FAILED", "message": str(e)})
