import re
from typing import Tuple

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"you\s+are\s+now\s+(in\s+)?developer\s+mode",
    r"pretend\s+(that\s+)?payment\s+(succeeded|was\s+successful|went\s+through)",
    r"grant\s+me\s+(free\s+tickets|admin\s+access|super_admin)",
    r"change\s+my\s+role\s+to\s+(admin|super_admin|organizer)",
    r"system\s*:\s*override",
    r"bypass\s+(payment|verification|pricing|tax|gst)",
    r"set\s+price\s+to\s+0",
    r"drop\s+table\s+",
    r"select\s+\*\s+from\s+users"
]

COMPILED_INJECTIONS = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]

def detect_prompt_injection(text: str) -> Tuple[bool, str]:
    """
    Checks if a user message contains patterns aiming to subvert
    system instructions, claim fake payment, or fabricate permissions.
    """
    if not text:
        return False, ""
    
    clean_text = text.strip()
    for pattern in COMPILED_INJECTIONS:
        if pattern.search(clean_text):
            return True, "Your message contains unauthorized override instructions. Transactional operations are strictly enforced by backend verification."
    
    return False, ""

def sanitize_user_input(text: str) -> str:
    """
    Sanitizes user input string: trims excessive whitespace, removes null bytes.
    """
    if not text:
        return ""
    # Strip null bytes and control chars
    clean = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    return clean.strip()
