from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

# ---------------------------------------------------------
# Tool Input Argument Schemas (Strict Pydantic Validation)
# ---------------------------------------------------------

class SearchEventsArgs(BaseModel):
    query: Optional[str] = Field(default=None, description="Keywords to search for event titles, descriptions, or artists")
    category: Optional[str] = Field(default=None, description="Category filter such as Technology, Comedy, Music, Workshop, Gaming, Business")
    city: Optional[str] = Field(default=None, description="City or location name such as Bengaluru, Bangalore, Mangaluru, Mangalore, Mumbai, Delhi")
    max_price: Optional[float] = Field(default=None, description="Maximum budget or ticket price limit in INR")
    date_filter: Optional[str] = Field(default=None, description="Timeframe like 'this weekend', 'today', 'tomorrow', 'saturday', 'sunday', or a specific date")

class GetEventDetailsArgs(BaseModel):
    event_id: int = Field(..., description="The unique integer ID of the event")

class GetEventTiersArgs(BaseModel):
    event_id: int = Field(..., description="The unique integer ID of the event")

class CompareEventsArgs(BaseModel):
    event_id_1: int = Field(..., description="First event ID to compare")
    event_id_2: int = Field(..., description="Second event ID to compare")

class CheckAvailabilityArgs(BaseModel):
    event_id: int = Field(..., description="The unique integer ID of the event")
    tier_name: Optional[str] = Field(default=None, description="Specific ticket tier name (e.g., VIP, Standard, Early Bird)")

class GetTicketPriceArgs(BaseModel):
    event_id: int = Field(..., description="The unique integer ID of the event")
    tier_name: Optional[str] = Field(default="Standard", description="The tier name (e.g. Standard, VIP)")
    quantity: int = Field(default=1, ge=1, le=20, description="Number of tickets requested")

class CreateBookingDraftArgs(BaseModel):
    event_id: int = Field(..., description="The unique integer ID of the event to book")
    tier_name: Optional[str] = Field(default="Standard", description="Name of the chosen tier (e.g. Standard, VIP, Pass)")
    quantity: int = Field(default=1, ge=1, le=10, description="Quantity of tickets to hold and reserve")

class UpdateBookingDraftArgs(BaseModel):
    draft_id: Optional[int] = Field(default=None, description="ID of the draft to update. If omitted, the active session draft is used.")
    quantity: Optional[int] = Field(default=None, ge=1, le=10, description="New ticket quantity requested")
    tier_name: Optional[str] = Field(default=None, description="New ticket tier name if changing tier")

class RemoveBookingItemArgs(BaseModel):
    draft_id: Optional[int] = Field(default=None, description="Draft ID to cancel and release held seats for")

class ApplyPromoCodeArgs(BaseModel):
    promo_code: str = Field(..., description="Coupon code to apply (e.g., STUDENT15, EARLYBIRD)")
    draft_id: Optional[int] = Field(default=None, description="Draft ID to apply code to. Uses active session draft if omitted.")

class RemovePromoCodeArgs(BaseModel):
    draft_id: Optional[int] = Field(default=None, description="Draft ID to remove promo from")

class CalculateBookingTotalArgs(BaseModel):
    event_id: int = Field(..., description="The unique integer ID of the event")
    tier_name: Optional[str] = Field(default="Standard", description="Ticket tier name")
    quantity: int = Field(default=1, ge=1, le=10, description="Number of tickets")
    promo_code: Optional[str] = Field(default=None, description="Optional promo code to test")

class CreatePaymentOrderArgs(BaseModel):
    draft_id: Optional[int] = Field(default=None, description="Draft ID for which to initiate payment. Uses active session draft if omitted.")

class GetBookingStatusArgs(BaseModel):
    draft_id_or_number: Optional[str] = Field(default=None, description="Draft ID or Draft Number (e.g. DFT-XXXXX)")

class GetUserBookingsArgs(BaseModel):
    limit: int = Field(default=5, ge=1, le=20, description="Maximum bookings to fetch")

class GetUserTicketsArgs(BaseModel):
    limit: int = Field(default=5, ge=1, le=20, description="Maximum confirmed tickets to fetch")

class GetTicketDetailsArgs(BaseModel):
    ticket_id_or_number: str = Field(..., description="Ticket ID or Ticket Number (e.g. TCK-XXXXX)")

class CancelBookingArgs(BaseModel):
    ticket_id: int = Field(..., description="The unique integer ID of the ticket to cancel and refund")
    reason: Optional[str] = Field(default=None, description="Optional cancellation reason")

class TransferTicketArgs(BaseModel):
    ticket_id: int = Field(..., description="The integer ID of the confirmed ticket to transfer")
    recipient_email: str = Field(..., description="Email address of the recipient")

class JoinWaitlistArgs(BaseModel):
    event_id: int = Field(..., description="The event ID to join waitlist for")
    tier_name: Optional[str] = Field(default="Standard", description="Tier name")
    quantity: int = Field(default=1, ge=1, le=10, description="Desired quantity")

class LeaveWaitlistArgs(BaseModel):
    waitlist_id: int = Field(..., description="The waitlist entry ID to remove")

class GetWaitlistStatusArgs(BaseModel):
    event_id: int = Field(..., description="The event ID")

class GetEventRecommendationsArgs(BaseModel):
    category: Optional[str] = Field(default=None, description="Optional category interest")
    limit: int = Field(default=4, ge=1, le=10, description="Max recommendations to return")


# ---------------------------------------------------------
# Tool Result Envelope
# ---------------------------------------------------------

class ToolResult(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None


# ---------------------------------------------------------
# Structured UI Components & AI Agent Response Models
# ---------------------------------------------------------

class UIComponent(BaseModel):
    type: str  # event_carousel, booking_summary, payment_button, ticket_confirmation, my_tickets_list, cancellation_card, create_event_entry
    data: Dict[str, Any]

class ConversationStateSnapshot(BaseModel):
    conversation_id: Optional[int] = None
    selected_event_id: Optional[int] = None
    selected_tier_name: Optional[str] = None
    quantity: Optional[int] = None
    booking_draft_id: Optional[int] = None
    active_hold_expires_at: Optional[str] = None
    promo_code: Optional[str] = None
    payment_status: Optional[str] = None
    last_event_result_ids: List[int] = []
    last_action: Optional[str] = None

class AgentResponse(BaseModel):
    conversation_id: Optional[int] = None
    message_id: Optional[str] = None
    message: str
    reply: str  # Backward-compatible alias
    ui: List[UIComponent] = []
    state: Dict[str, Any] = {}
    type: str = "text"  # Backward-compatible primary card type
    payload: Optional[Dict[str, Any]] = None  # Backward-compatible primary card payload
    quick_replies: Optional[List[Dict[str, str]]] = None
    intent: Optional[str] = "ai_agent"
    grounding_status: str = "GROUNDED_LIVE_DB"
