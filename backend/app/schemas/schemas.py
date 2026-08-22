from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

class UserCreate(BaseModel):
    email: str
    name: str
    password: str
    role: Optional[str] = "customer"
    phone: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    role: str
    phone: Optional[str] = None
    referral_code: Optional[str] = None

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class LoginRequest(BaseModel):
    email: str
    password: str

class TicketTypeItem(BaseModel):
    name: str = "Standard"
    price: float = 0.0
    quantity: int = 100

class EventCreate(BaseModel):
    title: str
    description: str
    category: str = "Tech"
    location: str
    venue: Optional[str] = None
    address: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    date_str: str
    price: float = 0.0
    total_capacity: int = 100
    image_url: Optional[str] = None
    cancellation_policy: Optional[str] = "Standard 24-hour cancellation policy applies."
    ticket_types: Optional[List[Dict[str, Any]]] = []
    max_tickets_per_booking: Optional[int] = 10
    lat: Optional[float] = None
    lng: Optional[float] = None
    status: Optional[str] = "DRAFT"
    tags: Optional[List[str]] = []

class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    location: Optional[str] = None
    venue: Optional[str] = None
    address: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    date_str: Optional[str] = None
    price: Optional[float] = None
    total_capacity: Optional[int] = None
    image_url: Optional[str] = None
    cancellation_policy: Optional[str] = None
    ticket_types: Optional[List[Dict[str, Any]]] = None
    max_tickets_per_booking: Optional[int] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    status: Optional[str] = None
    tags: Optional[List[str]] = None

class EventResponse(BaseModel):
    id: int
    title: str
    description: str
    category: str
    location: str
    venue: Optional[str] = None
    address: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    date_str: str
    price: float
    total_capacity: int
    available_tickets: int
    organizer_id: Optional[int] = None
    status: str = "PUBLISHED"
    image_url: Optional[str] = None
    cancellation_policy: Optional[str] = None
    ticket_types: Optional[List[Dict[str, Any]]] = []
    max_tickets_per_booking: Optional[int] = 10
    lat: Optional[float] = None
    lng: Optional[float] = None
    tags: Optional[List[str]] = []

    class Config:
        from_attributes = True

class RegisterRequest(BaseModel):
    email: str
    name: str
    password: str
    role: Optional[str] = "customer"
    phone: Optional[str] = None

class VerifyRequest(BaseModel):
    qr_token: Optional[str] = None
    ticket_number: Optional[str] = None
    event_id: Optional[Any] = None

class CheckInRequest(BaseModel):
    ticket_id: Optional[int] = None
    ticket_number: Optional[str] = None
    staff_id: Optional[str] = "#STAFF-001"

class OrganizerApplicationRequest(BaseModel):
    organization_name: str
    description: Optional[str] = None
    website: Optional[str] = None


class BookingCreate(BaseModel):
    event_id: int
    tier_id: Optional[int] = None
    ticket_type: Optional[str] = "General"
    quantity: int = 1
    idempotency_key: Optional[str] = None
    coupon_code: Optional[str] = None

class BookingResponse(BaseModel):
    booking_id: Optional[int] = None
    ticket_id: Optional[int] = None
    ticket_number: Optional[str] = None
    event_title: str
    price_paid: float
    status: str
    invoice_number: Optional[str] = None
    qr_code_url: Optional[str] = None
    tickets: Optional[List[Dict[str, Any]]] = None

class ChatRequest(BaseModel):
    message: Optional[str] = ""
    user_id: Optional[int] = 1
    conversation_id: Optional[int] = None
    event_type: Optional[str] = "user_message" # user_message or system_event
    payload: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    reply: str
    intent: str
    confidence: float
    routed_to: str
    grounding_status: str
    type: Optional[str] = "text"
    payload: Optional[Dict[str, Any]] = None
    quick_replies: Optional[List[Dict[str, str]]] = None
    conversation_id: Optional[int] = None

class PaymentOrderRequest(BaseModel):
    event_id: int
    ticket_type: Optional[str] = "Standard"
    quantity: int = 1

class PaymentVerifyRequest(BaseModel):
    razorpay_order_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None
    razorpay_signature: Optional[str] = None
    booking_id: Optional[int] = None
    user_id: Optional[int] = 1

class FraudFlagResponse(BaseModel):
    id: int
    user_id: int
    booking_id: Optional[int] = None
    score: float
    reason: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class TransferRequest(BaseModel):
    recipient_email: str

class DraftRequest(BaseModel):
    bullet_points: str

class BroadcastRequest(BaseModel):
    message: str
    priority: Optional[str] = "high"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class HoldSeatsRequest(BaseModel):
    seat_codes: List[str]
    section_name: Optional[str] = "Main Floor"


class SeatResponse(BaseModel):
    id: int
    event_id: int
    section_name: str
    row_label: str
    seat_number: int
    seat_code: str
    status: str
    price: float

    class Config:
        from_attributes = True


class SeatMapResponse(BaseModel):
    event_id: int
    sections: Dict[str, List[SeatResponse]]


class WaitlistCreateRequest(BaseModel):
    ticket_tier: Optional[str] = "Standard"
    requested_quantity: Optional[int] = 1


class RefundCreateRequest(BaseModel):
    ticket_id: int
    quantity_refunded: Optional[int] = 1
    reason: Optional[str] = ""



class RefundReviewRequest(BaseModel):
    status: str  # APPROVED or REJECTED
    amount_approved: Optional[float] = 0.0
    rejection_reason: Optional[str] = ""


class PromoApplyRequest(BaseModel):
    code: str
    event_id: int
    ticket_type: Optional[str] = "Standard"
    quantity: Optional[int] = 1
    subtotal: float


class PromoCreateRequest(BaseModel):
    code: str
    discount_type: str = "PERCENTAGE"  # PERCENTAGE or FIXED
    discount_value: float
    max_uses: Optional[int] = 100
    per_user_limit: Optional[int] = 1
    min_order_amount: Optional[float] = 0.0
    max_discount_amount: Optional[float] = None
    expiry_date: Optional[str] = None


class TransferInitiateRequest(BaseModel):
    recipient_email: str


class SupportTicketCreateRequest(BaseModel):
    category: str
    subject: str
    description: str
    event_id: Optional[int] = None
    booking_ticket_id: Optional[int] = None


class SupportMessageRequest(BaseModel):
    message: str


class AnnouncementCreateRequest(BaseModel):
    title: str
    message: str


class TeamMemberInviteRequest(BaseModel):
    email: str
    role: str = "VIEWER"
    permissions: Optional[List[str]] = []


class EventCompareRequest(BaseModel):
    event_ids: List[int]


