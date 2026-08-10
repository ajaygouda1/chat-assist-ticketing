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
    quantity: int = 1
    idempotency_key: Optional[str] = None

class BookingResponse(BaseModel):
    ticket_id: int
    ticket_number: str
    event_title: str
    price_paid: float
    status: str
    invoice_number: Optional[str] = None
    qr_code_url: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    user_id: Optional[int] = 1

class ChatResponse(BaseModel):
    reply: str
    intent: str
    confidence: float
    routed_to: str
    grounding_status: str
    type: Optional[str] = "text"
    payload: Optional[Dict[str, Any]] = None
    quick_replies: Optional[List[Dict[str, str]]] = None

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

