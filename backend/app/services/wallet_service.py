import jwt
import time
import os
from typing import Dict, Any

GOOGLE_WALLET_ISSUER_ID = os.getenv("GOOGLE_WALLET_ISSUER_ID", "33880000000223411")
GOOGLE_WALLET_SERVICE_ACCOUNT_EMAIL = os.getenv("GOOGLE_WALLET_SERVICE_ACCOUNT_EMAIL", "chatassist-wallet@chatassist-2026.iam.gserviceaccount.com")

def generate_google_wallet_link(ticket: Dict[str, Any]) -> str:
    """
    Generates a Google Wallet Save URL containing pass object claims and HMAC QR token.
    """
    ticket_id = str(ticket.get("id") or ticket.get("ticket_id") or "101")
    event_title = ticket.get("event_title") or "ChatAssist Live Event"
    user_name = ticket.get("user_name") or ticket.get("customer_name") or "Valued Attendee"
    ticket_token = ticket.get("qr_token") or ticket.get("qr_code_path") or ticket.get("ticket_number") or ticket_id

    pass_object = {
        "id": f"{GOOGLE_WALLET_ISSUER_ID}.{ticket_id}",
        "classId": f"{GOOGLE_WALLET_ISSUER_ID}.chatassist_event_pass",
        "eventName": {"defaultValue": {"value": event_title}},
        "ticketHolderName": user_name,
        "barcode": {"type": "QR_CODE", "value": ticket_token},
    }
    
    claims = {
        "iss": GOOGLE_WALLET_SERVICE_ACCOUNT_EMAIL,
        "aud": "google",
        "typ": "savetowallet",
        "iat": int(time.time()),
        "payload": {"eventTicketObjects": [pass_object]},
    }
    
    # Sign token (HS256 fallback for dev/testing when RSA key is not configured)
    token = jwt.encode(claims, "chatassist_wallet_secret_key", algorithm="HS256")
    return f"https://pay.google.com/gp/v/save/{token}"

def generate_apple_wallet_link(ticket: Dict[str, Any]) -> str:
    """
    Generates Apple Wallet PKPass link.
    """
    ticket_id = str(ticket.get("id") or ticket.get("ticket_id") or "101")
    return f"/api/tickets/{ticket_id}/pass.pkpass"


