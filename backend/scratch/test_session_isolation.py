import sys
import os
from pathlib import Path

# Add backend directory to sys.path
backend_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_path))

from app.db.session import SessionLocal
from app.services.openai_service import process_chat_message
from app.services.booking_conversation import get_booking_session, ConversationMode, BookingState

def run_session_isolation_test():
    print("==========================================")
    print("TESTING CHATASSIST MULTI-SESSION ISOLATION")
    print("==========================================")

    db = SessionLocal()
    user_id = 1
    conv_a_id = 101
    conv_b_id = 102

    try:
        # Step 1: Conversation A - Search and start booking 2 VIP passes
        print("\n--- Conversation A (#101) ---")
        msg_a1 = "Book 2 VIP passes for the 1st event"
        res_a1 = process_chat_message(user_id=user_id, message=msg_a1, db=db, conversation_id=conv_a_id)
        
        session_a = get_booking_session(user_id, conv_a_id)
        print(f"Conversation A State: Mode={session_a.mode.value}, State={session_a.state.value}, Qty={session_a.quantity}")
        print(f"Conversation A Response Type: {res_a1.get('type')}")
        
        assert session_a.mode == ConversationMode.BOOKING, "Conv A mode should be BOOKING"
        assert session_a.quantity == 2, "Conv A quantity should be 2"
        print("[OK] Conversation A is in BOOKING mode with 2 tickets.")

        # Step 2: Conversation B - Create a tech workshop event
        print("\n--- Conversation B (#102) ---")
        msg_b1 = "Create a tech workshop event"
        res_b1 = process_chat_message(user_id=user_id, message=msg_b1, db=db, conversation_id=conv_b_id)

        session_b = get_booking_session(user_id, conv_b_id)
        print(f"Conversation B State: Mode={session_b.mode.value}, State={session_b.state.value}")
        print(f"Conversation B Response Type: {res_b1.get('type')}")

        assert session_b.mode == ConversationMode.EVENT_CREATION, "Conv B mode should be EVENT_CREATION"
        assert res_b1.get("type") == "event_creation_card", "Conv B type should be event_creation_card"
        assert "payment_button" not in str(res_b1), "Conv B should NOT contain payment buttons"
        print("[OK] Conversation B is in EVENT_CREATION mode with no booking/payment bleed.")

        # Step 3: Re-verify Conversation A is unchanged
        print("\n--- Re-verifying Conversation A (#101) ---")
        session_a_again = get_booking_session(user_id, conv_a_id)
        print(f"Conversation A State: Mode={session_a_again.mode.value}, State={session_a_again.state.value}, Qty={session_a_again.quantity}")
        
        assert session_a_again.mode == ConversationMode.BOOKING, "Conv A mode must remain BOOKING"
        assert session_a_again.quantity == 2, "Conv A quantity must remain 2"
        print("[OK] Conversation A draft state remained 100% isolated and intact!")

        print("\n==========================================")
        print("MULTI-SESSION ISOLATION TEST PASSED 100%!")
        print("==========================================")

    finally:
        db.close()

if __name__ == "__main__":
    run_session_isolation_test()
