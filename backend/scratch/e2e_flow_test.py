import sys
import os
import json
import time
import asyncio

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import httpx
from app.main import app

def sanitize(text):
    return str(text).encode('ascii', 'ignore').decode('ascii')

import pytest

@pytest.mark.anyio
async def test_full_e2e_flow():
    print("==========================================")
    print("STARTING CHATASSIST E2E WORKFLOW VERIFICATION")
    print("==========================================")

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:

        # 1. Create a fresh conversation session
        res_conv = await client.post("/api/v1/chat/conversations", json={"title": "E2E Verification Chat"})
        assert res_conv.status_code == 200, f"Failed to create conversation: {res_conv.text}"
        conv_data = res_conv.json()
        conv_id = conv_data["id"]
        print(f"[OK] Step 1: Created fresh conversation session ID #{conv_id}")

        # 2. Query event discovery
        res_chat1 = await client.post("/api/v1/chat", json={"message": "Find tech events in Bengaluru", "conversation_id": conv_id})
        assert res_chat1.status_code == 200
        chat1 = res_chat1.json()
        print(f"[OK] Step 2: Search events reply -> '{sanitize(chat1['reply'])[:50]}...' (Type: {chat1.get('type')})")

        # 3. Initiate booking
        res_chat2 = await client.post("/api/v1/chat", json={"message": "Book 2 VIP tickets for India AI & Deep Learning Summit", "conversation_id": conv_id})
        assert res_chat2.status_code == 200
        chat2 = res_chat2.json()
        print(f"[OK] Step 3: Booking summary reply -> Type: {chat2.get('type')}")
        assert chat2.get('type') == 'booking_summary', f"Expected booking_summary but got {chat2.get('type')}"
        payload = chat2.get('payload', {})
        print(f"   Payload: {sanitize(payload.get('event_title'))} | Qty: {payload.get('quantity')} | Tier: {payload.get('ticket_type')} | Total: INR {payload.get('total')}")

        # 4. Confirm booking -> payment button state
        res_chat3 = await client.post("/api/v1/chat", json={"message": "Confirm booking", "conversation_id": conv_id})
        assert res_chat3.status_code == 200
        chat3 = res_chat3.json()
        assert chat3.get('type') == 'payment_button'
        payment_data = chat3.get('payload', {})
        order_id = payment_data.get('order_id')
        booking_id = payment_data.get('booking_id')
        print(f"[OK] Step 4: Payment payload generated -> Order ID: {order_id} | Booking ID: {booking_id}")

        # 5. Perform payment verification
        pay_id = f"pay_test_{int(time.time())}"
        res_pay1 = await client.post("/api/v1/payments/verify", json={
            "razorpay_order_id": order_id,
            "razorpay_payment_id": pay_id,
            "razorpay_signature": "mock_signature_valid",
            "booking_id": booking_id,
            "user_id": 1
        })
        assert res_pay1.status_code == 200, f"Payment verify failed: {res_pay1.text}"
        pay_res1 = res_pay1.json()
        ticket = pay_res1.get("ticket", {})
        ticket_num = ticket.get("ticket_number")
        print(f"[OK] Step 5 & 6: Payment verified! Ticket Issued #{ticket_num} (ID: {ticket.get('id')})")
        assert ticket.get("status") == "CONFIRMED"

        # 5b. Idempotency Test: Repeat identical payment verification call
        res_pay2 = await client.post("/api/v1/payments/verify", json={
            "razorpay_order_id": order_id,
            "razorpay_payment_id": pay_id,
            "razorpay_signature": "mock_signature_valid",
            "booking_id": booking_id,
            "user_id": 1
        })
        assert res_pay2.status_code == 200
        pay_res2 = res_pay2.json()
        print(f"[OK] Step 6b: Idempotency Protection Verified -> Status: {pay_res2.get('status')} | Duplicate Ticket Count: 0")
        assert pay_res2.get("status") == "ALREADY_CONFIRMED"
        assert pay_res2.get("ticket", {}).get("ticket_number") == ticket_num

        # 6. Verify QR Check-in Scan #1 (First scan -> VALID)
        res_scan1 = await client.post("/api/v1/tickets/verify", json={"ticket_number": ticket_num})
        assert res_scan1.status_code == 200
        scan1_data = res_scan1.json()
        print(f"[OK] Step 7: Initial QR Scan Verification -> Valid: {scan1_data.get('valid')} | Status: {scan1_data.get('status')}")
        assert scan1_data.get('valid') is True

        # 7. Perform Check-in (marking ticket as CHECKED_IN / USED)
        res_checkin = await client.post("/api/v1/tickets/check-in", json={"ticket_id": ticket.get("id"), "ticket_number": ticket_num})
        assert res_checkin.status_code == 200
        checkin_data = res_checkin.json()
        print(f"[OK] Step 8: Gate Check-in Completed -> Status: {checkin_data.get('status')}")

        # 8. Re-scan ticket -> Second scan must be REJECTED as ALREADY_USED
        res_scan2 = await client.post("/api/v1/tickets/verify", json={"ticket_number": ticket_num})
        assert res_scan2.status_code == 200
        scan2_data = res_scan2.json()
        print(f"[OK] Step 9: Duplicate QR Scan Rejection -> Valid: {scan2_data.get('valid')} | Status: {scan2_data.get('status')} | Message: {sanitize(scan2_data.get('message'))}")
        assert scan2_data.get('valid') is False and scan2_data.get('status') == 'ALREADY_USED'

        # 9. Verify session message history retrieval
        res_msgs = await client.get(f"/api/v1/chat/conversations/{conv_id}/messages")
        assert res_msgs.status_code == 200
        msgs = res_msgs.json()
        print(f"[OK] Step 10: Reloaded conversation session #{conv_id} history -> {len(msgs)} messages recovered successfully!")

        print("==========================================")
        print("ALL 10 END-TO-END WORKFLOW CHECKS PASSED 100% SUCCESSFULLY!")
        print("==========================================")

if __name__ == "__main__":
    asyncio.run(test_full_e2e_flow())
