import re

def extract_event_slots(text: str) -> dict:
    """
    Slot extraction for event creation from free-form text.
    Extracts price, capacity/seats, date, and title.
    """
    slots = {
        "title": None,
        "event_name": None,
        "category": None,
        "event_type": None,
        "price": None,
        "capacity": None,
        "quantity": None,
        "ticket_type": None,
        "date": None,
        "date_str": None,
        "location": None,
        "city": None,
        "venue": None
    }


    # Quantity extraction (e.g., 5 tickets, 8 VIP Pass tickets, make it 7, book ten)
    WORD_NUMBERS = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10
    }

    text_lower = text.lower()
    qty_found = None

    # Strip ordinals before quantity search to prevent "first one" matching "one" as quantity = 1
    text_no_ordinals = re.sub(r'\b(first|second|third|fourth|fifth|1st|2nd|3rd|4th|5th)\s*(one|event)?\b', '', text_lower)

    # First check digits in the ordinal-cleaned text
    numbers = re.findall(r'\b(\d+)\b', text_no_ordinals)
    valid_qtys = [int(n) for n in numbers if 1 <= int(n) <= 50]
    if valid_qtys:
        qty_found = valid_qtys[0]

    # If no digit quantity found, check word numbers in ordinal-cleaned text
    if not qty_found:
        for word, num in WORD_NUMBERS.items():
            if re.search(r'\b' + word + r'\b', text_no_ordinals):
                qty_found = num
                break

    slots["quantity"] = qty_found

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

    # Category & Event Type extraction
    if re.search(r'\b(tech|technology|ai|coding|software|hackathon)\b', text, re.IGNORECASE):
        slots["category"] = "Technology"
    elif re.search(r'\b(music|concert|dj|band|live music)\b', text, re.IGNORECASE):
        slots["category"] = "Music"
    elif re.search(r'\b(conference|summit|meetup|symposium)\b', text, re.IGNORECASE):
        slots["category"] = "Conference"
    elif re.search(r'\b(workshop|masterclass|training|bootcamp)\b', text, re.IGNORECASE):
        slots["category"] = "Workshop"

    if re.search(r'\bworkshop\b', text, re.IGNORECASE):
        slots["event_type"] = "Workshop"
    elif re.search(r'\bconference\b', text, re.IGNORECASE):
        slots["event_type"] = "Conference"
    elif re.search(r'\bhackathon\b', text, re.IGNORECASE):
        slots["event_type"] = "Hackathon"
    elif re.search(r'\bconcert\b', text, re.IGNORECASE):
        slots["event_type"] = "Concert"

    # City extraction (e.g. Bengaluru, Mangaluru, Mumbai, Delhi, Hyderabad)
    city_match = re.search(r'\b(bengaluru|bangalore|mangaluru|mangalore|mumbai|delhi|hyderabad|pune|chennai)\b', text, re.IGNORECASE)
    if city_match:
        slots["city"] = city_match.group(1).title()

    # Title extraction (e.g. called CodeFest 2026, titled Tech Summit)
    title_match = re.search(r'(?:called|titled|named)\s+([A-Za-z0-9\s&]+?)(?:in|on|at|with|\.|$)', text, re.IGNORECASE)
    if title_match:
        slots["title"] = title_match.group(1).strip()
        slots["event_name"] = slots["title"]

    return slots

