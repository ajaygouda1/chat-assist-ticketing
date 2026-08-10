import re

def extract_event_slots(text: str) -> dict:
    """
    Slot extraction for event creation from free-form text.
    Extracts price, capacity/seats, date, and title.
    """
    slots = {
        "title": None,
        "event_name": None,
        "price": 0.0,
        "capacity": 100,
        "quantity": 1,
        "ticket_type": "Standard",
        "date": "2026-09-15",
        "location": "Main Auditorium"
    }

    # Quantity extraction (e.g., 2 tickets, 3 VIP Pass tickets, 1 seat, buy 2)
    # Extract any 1-2 digit standalone integer between 1 and 50 (ignores years like 2026)
    numbers = re.findall(r'\b(\d+)\b', text)
    valid_qtys = [int(n) for n in numbers if 1 <= int(n) <= 50]
    if valid_qtys:
        slots["quantity"] = valid_qtys[0]
    else:
        slots["quantity"] = None

    # Ticket Type extraction (e.g., VIP, Standard, Early Bird)
    if re.search(r'\bVIP\b', text, re.IGNORECASE):
        slots["ticket_type"] = "VIP Pass"
    elif re.search(r'\bEarly\s*Bird\b', text, re.IGNORECASE):
        slots["ticket_type"] = "Early Bird"
    elif re.search(r'\bStandard\b', text, re.IGNORECASE):
        slots["ticket_type"] = "Standard"

    # Price extraction (e.g., ₹299, Rs 500, 299 INR)
    price_match = re.search(r'(?:₹|Rs\.?|INR)\s*(\d+)|(\d+)\s*(?:INR|rupees)', text, re.IGNORECASE)
    if price_match:
        val = price_match.group(1) or price_match.group(2)
        slots["price"] = float(val)

    # Capacity extraction (e.g., 500 seats, capacity of 200)
    cap_match = re.search(r'(\d+)\s*(?:seats|capacity|tickets|people)', text, re.IGNORECASE)
    if cap_match:
        slots["capacity"] = int(cap_match.group(1))

    # Location extraction (e.g., at XYZ college, at MG Road)
    loc_match = re.search(r'at\s+([A-Za-z0-9\s,]+?)(?:,|\.|$|on|\d{1,2})', text, re.IGNORECASE)
    if loc_match:
        slots["location"] = loc_match.group(1).strip()

    # Event name extraction (e.g., for AI summit, for DevFest)
    name_match = re.search(r'(?:for|of|to)\s+([A-Za-z0-9\s&]+)', text, re.IGNORECASE)
    if name_match:
        slots["event_name"] = name_match.group(1).strip()

    return slots
