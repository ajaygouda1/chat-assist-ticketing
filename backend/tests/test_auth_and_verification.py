import sys
import os
import uuid
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


from app.core.database import SessionLocal, engine, Base
from app.models.user import User
from app.models.ticket import Event, Ticket
from app.api.v1.tickets import verify_ticket
from app.schemas.schemas import VerifyRequest, UserCreate, LoginRequest
from app.api.v1.auth import register, login
from app.core.security import verify_password
from app.core.authorization import require_event_owner
from fastapi import HTTPException

def test_auth_and_verification():
    db = SessionLocal()

    print("\n--- 1. TESTING VERIFICATION WITH 'ALL EVENTS' (NO SCOPE FILTER) ---")
    ev1 = Event(title="Event Alpha", description="Test Event Description 1", location="Venue Alpha", date_str="15 Sep 2026", price=100.0, available_tickets=10, total_capacity=10, status="PUBLISHED")
    ev2 = Event(title="Event Beta", description="Test Event Description 2", location="Venue Beta", date_str="16 Sep 2026", price=200.0, available_tickets=10, total_capacity=10, status="PUBLISHED")

    db.add_all([ev1, ev2])
    db.commit()
    db.refresh(ev1)
    db.refresh(ev2)

    t1 = Ticket(ticket_number=f"TCK-{uuid.uuid4().hex[:6].upper()}", event_id=ev1.id, user_id=1, status="CONFIRMED", price_paid=100.0)
    db.add(t1)
    db.commit()
    db.refresh(t1)

    # Test 1a: Scoped to matching event
    res = verify_ticket(req=VerifyRequest(ticket_number=t1.ticket_number, event_id=ev1.id), db=db)
    assert res["valid"] is True, f"Expected valid ticket for matching event_id, got: {res}"

    # Test 1b: Scoped to wrong event (should fail with INVALID_EVENT)
    res_mismatch = verify_ticket(req=VerifyRequest(ticket_number=t1.ticket_number, event_id=ev2.id), db=db)
    assert res_mismatch["valid"] is False
    assert res_mismatch["status"] == "INVALID_EVENT"

    # Test 1c: "All Events" filter variations (None, "", "ALL", "All Events (No Scope Filter)")
    for scope_val in [None, "", "ALL", "all", "All Events", "All Events (No Scope Filter)", 0]:
        res_no_scope = verify_ticket(req=VerifyRequest(ticket_number=t1.ticket_number, event_id=scope_val), db=db)
        assert res_no_scope["valid"] is True, f"Failed for scope_val '{scope_val}': {res_no_scope}"
        print(f"Verified ticket with scope setting '{scope_val}' -> PASS")

    print("\n--- 2. TESTING AUTH REGISTER & LOGIN ---")
    test_email = f"user_{uuid.uuid4().hex[:4]}@example.com"
    reg_req = UserCreate(email=test_email, name="Test User", password="password123")
    token_res = register(user_in=reg_req, db=db)
    assert "access_token" in token_res
    assert token_res["user"].email == test_email
    print("User Registration -> PASS")

    login_req = LoginRequest(email=test_email, password="password123")
    login_res = login(creds=login_req, db=db)
    assert "access_token" in login_res
    print("User Login -> PASS")

    print("\n--- 3. TESTING EVENT OWNERSHIP AUTHORIZATION (§54d) ---")
    org_user = User(email=f"org_{uuid.uuid4().hex[:4]}@test.com", name="Org User", hashed_password="pwd", role="organizer")
    other_org = User(email=f"other_{uuid.uuid4().hex[:4]}@test.com", name="Other Org", hashed_password="pwd", role="organizer")
    admin_user = User(email=f"admin_{uuid.uuid4().hex[:4]}@test.com", name="Super Admin", hashed_password="pwd", role="super_admin")
    db.add_all([org_user, other_org, admin_user])
    db.commit()

    org_event = Event(title="Org Private Event", description="Private event description", location="Private Hall", date_str="18 Sep 2026", price=50.0, available_tickets=50, total_capacity=50, status="DRAFT", organizer_id=org_user.id)
    db.add(org_event)
    db.commit()
    db.refresh(org_event)


    # Owner can access
    allowed = require_event_owner(event_id=org_event.id, current_user=org_user, db=db)
    assert allowed.id == org_event.id
    print("Event Owner Access -> ALLOWED PASS")

    # Super Admin can access
    allowed_admin = require_event_owner(event_id=org_event.id, current_user=admin_user, db=db)
    assert allowed_admin.id == org_event.id
    print("Super Admin Access to Event -> ALLOWED PASS")

    # Other organizer cannot access (raises 403)
    try:
        require_event_owner(event_id=org_event.id, current_user=other_org, db=db)
        assert False, "Should have raised 403 for unauthorized organizer"
    except HTTPException as exc:
        assert exc.status_code == 403
        print("Unauthorized Organizer Access -> BLOCKED (403 FORBIDDEN) PASS")

    print("\n✅ ALL AUTHENTICATION & ALL EVENTS VERIFICATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_auth_and_verification()
