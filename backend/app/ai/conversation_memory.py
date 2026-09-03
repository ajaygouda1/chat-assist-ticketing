from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.conversation import Conversation, ConversationMessage
from app.models.booking_draft import BookingDraft

class ConversationState:
    def __init__(self, conversation_id: int, user_id: int):
        self.conversation_id = conversation_id
        self.user_id = user_id
        self.selected_event_id: Optional[int] = None
        self.selected_tier_name: Optional[str] = "Standard"
        self.quantity: int = 1
        self.booking_draft_id: Optional[int] = None
        self.active_hold_expires_at: Optional[datetime] = None
        self.promo_code: Optional[str] = None
        self.payment_status: Optional[str] = None
        self.last_event_result_ids: List[int] = []
        self.last_action: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "conversation_id": self.conversation_id,
            "user_id": self.user_id,
            "selected_event_id": self.selected_event_id,
            "selected_tier_name": self.selected_tier_name,
            "quantity": self.quantity,
            "booking_draft_id": self.booking_draft_id,
            "active_hold_expires_at": self.active_hold_expires_at.isoformat() if self.active_hold_expires_at else None,
            "promo_code": self.promo_code,
            "payment_status": self.payment_status,
            "last_event_result_ids": self.last_event_result_ids,
            "last_action": self.last_action
        }

    def reset_booking(self):
        self.selected_event_id = None
        self.selected_tier_name = "Standard"
        self.quantity = 1
        self.booking_draft_id = None
        self.active_hold_expires_at = None
        self.promo_code = None
        self.payment_status = None


class ConversationMemoryManager:
    """
    Manages in-memory session cache and DB persistence for conversations.
    """
    def __init__(self):
        self._states: Dict[str, ConversationState] = {}

    def get_or_create_state(self, conversation_id: int, user_id: int, db: Optional[Session] = None) -> ConversationState:
        key = f"{user_id}_{conversation_id}"
        if key not in self._states:
            st = ConversationState(conversation_id, user_id)
            # Recover from active BookingDraft if available in DB
            if db:
                active_draft = db.query(BookingDraft).filter(
                    BookingDraft.user_id == user_id,
                    BookingDraft.conversation_id == conversation_id,
                    BookingDraft.status.in_(["DRAFT", "READY_FOR_PAYMENT"])
                ).order_by(BookingDraft.created_at.desc()).first()

                if active_draft and not active_draft.is_expired():
                    st.selected_event_id = active_draft.event_id
                    st.selected_tier_name = active_draft.ticket_type
                    st.quantity = active_draft.quantity
                    st.booking_draft_id = active_draft.id
                    st.active_hold_expires_at = active_draft.expires_at
                    st.last_action = "DRAFT_ACTIVE"

            self._states[key] = st
        return self._states[key]

    def get_recent_messages(self, conversation_id: int, db: Session, limit: int = 10) -> List[Dict[str, Any]]:
        msgs = db.query(ConversationMessage).filter(
            ConversationMessage.conversation_id == conversation_id
        ).order_by(ConversationMessage.created_at.desc()).limit(limit).all()

        formatted = []
        for m in reversed(msgs):
            role = "user" if m.sender == "user" else "assistant"
            formatted.append({
                "role": role,
                "content": m.message,
                "message_type": m.message_type,
                "metadata": m.metadata_json or {}
            })
        return formatted

memory_manager = ConversationMemoryManager()
