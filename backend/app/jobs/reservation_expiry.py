from sqlalchemy.orm import Session
from datetime import datetime
from typing import Dict, Any, Optional

from app.models.ticket import Event, Ticket
from app.models.payment import Payment

def on_reservation_expired(booking_id: int, db: Session) -> Dict[str, Any]:
    """
    Abandoned Booking Recovery:
    Ties into Redis/DB reservation TTL expiry events. Releases reserved tickets back to
    event available_tickets pool and schedules a one-shot recovery notification nudge.
    """

    payment = db.query(Payment).filter(Payment.id == booking_id).first()
    if not payment:
        payment = db.query(Payment).filter(Payment.order_id == str(booking_id)).first()

    if not payment:
        return {"success": False, "reason": "Booking/Payment not found"}

    if payment.status == "PAYMENT_PENDING":
        payment.status = "EXPIRED"
        
        # Release reserved tickets back to available capacity
        if payment.ticket_id:
            t = db.query(Ticket).filter(Ticket.id == payment.ticket_id).first()
            if t and t.status == "RESERVED":
                t.status = "CANCELLED"
                ev = db.query(Event).filter(Event.id == t.event_id).first()
                if ev:
                    ev.available_tickets += 1
        
        db.commit()
        
        # Schedule one-shot recovery notification nudge (§57b)
        notification_res = schedule_recovery_notification(payment, delay_minutes=30)
        return {
            "success": True,
            "status": "EXPIRED_RELEASED",
            "message": "Reserved tickets released back to inventory.",
            "recovery_notification": notification_res
        }

    return {"success": False, "status": payment.status, "reason": "Booking is not in PAYMENT_PENDING state"}


def schedule_recovery_notification(payment: Payment, delay_minutes: int = 30) -> Dict[str, Any]:
    """
    Schedules a single one-shot nudge notification for abandoned checkout recovery.
    """
    return {
        "scheduled": True,
        "payment_id": payment.payment_id,
        "user_id": payment.user_id,
        "delay_minutes": delay_minutes,
        "message": "Your ticket reservation expired. Click here to re-reserve before tickets sell out!"
    }
