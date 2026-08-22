from enum import Enum
from fastapi import HTTPException
from app.models.booking_draft import BookingDraft

class BookingStatus(str, Enum):
    CREATED = "CREATED"
    HELD = "HELD"
    PAYMENT_PENDING = "PAYMENT_PENDING"
    PAYMENT_VERIFIED = "PAYMENT_VERIFIED"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    REFUND_PENDING = "REFUND_PENDING"
    REFUNDED = "REFUNDED"
    EXPIRED = "EXPIRED"

VALID_BOOKING_TRANSITIONS = {
    BookingStatus.CREATED: [BookingStatus.HELD, BookingStatus.CANCELLED, BookingStatus.EXPIRED],
    BookingStatus.HELD: [BookingStatus.PAYMENT_PENDING, BookingStatus.EXPIRED, BookingStatus.CANCELLED],
    BookingStatus.PAYMENT_PENDING: [BookingStatus.PAYMENT_VERIFIED, BookingStatus.EXPIRED, BookingStatus.CANCELLED],
    BookingStatus.PAYMENT_VERIFIED: [BookingStatus.CONFIRMED, BookingStatus.REFUND_PENDING],
    BookingStatus.CONFIRMED: [BookingStatus.CANCELLED, BookingStatus.REFUND_PENDING, BookingStatus.REFUNDED],
    BookingStatus.REFUND_PENDING: [BookingStatus.REFUNDED, BookingStatus.CONFIRMED],
    BookingStatus.REFUNDED: [],
    BookingStatus.CANCELLED: [],
    BookingStatus.EXPIRED: []
}

def transition_booking_status(booking: BookingDraft, target_status: str) -> str:
    current = booking.status or "DRAFT"
    # Normalize DRAFT -> CREATED
    if current in ["DRAFT", "READY_FOR_PAYMENT"]:
        current = BookingStatus.CREATED.value

    target = target_status.upper()

    if target not in [s.value for s in BookingStatus]:
        raise HTTPException(status_code=400, detail=f"Invalid target booking status '{target_status}'")

    if current == target:
        return target

    allowed = [s.value for s in VALID_BOOKING_TRANSITIONS.get(BookingStatus(current), [])]
    if target not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid booking status transition from '{current}' to '{target}'. Allowed transitions: {allowed}"
        )

    booking.status = target
    return target
