class AIException(Exception):
    """Base exception for ChatAssist AI layer."""
    def __init__(self, code: str, message: str, user_friendly_message: str):
        super().__init__(message)
        self.code = code
        self.message = message
        self.user_friendly_message = user_friendly_message

class InsufficientInventoryError(AIException):
    def __init__(self, available: int, requested: int, tier_name: str = "Standard"):
        msg = f"Only {available} {tier_name} ticket(s) currently available, but {requested} requested."
        user_msg = f"Only {available} {tier_name} ticket(s) are left. Would you like to book {available} instead?"
        super().__init__("INSUFFICIENT_INVENTORY", msg, user_msg)
        self.available = available
        self.requested = requested

class EventNotFoundError(AIException):
    def __init__(self, event_id: int):
        msg = f"Event with ID #{event_id} not found or inactive."
        user_msg = "I couldn't find that event in our catalog. It may have been completed, postponed, or removed."
        super().__init__("EVENT_NOT_FOUND", msg, user_msg)

class HoldExpiredError(AIException):
    def __init__(self, draft_id: int):
        msg = f"Booking draft #{draft_id} hold expired."
        user_msg = "Your 10-minute ticket reservation expired. Would you like me to check real-time availability and hold fresh seats for you?"
        super().__init__("HOLD_EXPIRED", msg, user_msg)

class PaymentVerificationError(AIException):
    def __init__(self, reason: str = "Signature mismatch"):
        msg = f"Payment signature verification failed: {reason}"
        user_msg = "I couldn't verify the payment signature with the payment gateway. Your booking has not been confirmed."
        super().__init__("PAYMENT_VERIFICATION_FAILED", msg, user_msg)

class UnauthorizedActionError(AIException):
    def __init__(self, action: str):
        msg = f"Unauthorized action: {action}"
        user_msg = "You don't have permission to perform this action. Please log in with the required account privileges."
        super().__init__("UNAUTHORIZED_ACTION", msg, user_msg)
