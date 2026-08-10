import sys
import os
import concurrent.futures
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

try:
    import pytest
except ImportError:
    pytest = None


import tempfile

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import Base
from app.models.ticket import Event, Ticket
from app.models.user import User

TEST_DB_PATH = os.path.join(tempfile.gettempdir(), "test_concurrency.db").replace("\\", "/")
TEST_DB_URL = f"sqlite:///{TEST_DB_PATH}"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def setup_test_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    # Create test user
    user = User(email="test@user.com", name="Test User", hashed_password="pwd", role="customer")
    db.add(user)
    
    # Create test event with ONLY 3 available tickets
    event = Event(
        title="High Demand Concurrency Summit",
        description="Limited capacity test event",
        category="Tech",
        location="Lab Arena",
        date_str="Tonight",
        price=100.0,
        total_capacity=3,
        available_tickets=3
    )
    db.add(event)
    db.commit()
    event_id = event.id
    db.close()
    return event_id

def attempt_booking(event_id: int, user_id: int, thread_idx: int):
    """Simulates single booking attempt inside isolated DB session using atomic SQL UPDATE."""
    db = TestingSessionLocal()
    success = False
    error_msg = ""
    try:
        # Atomic decrement update
        rows_updated = db.query(Event).filter(
            Event.id == event_id,
            Event.available_tickets >= 1
        ).update({Event.available_tickets: Event.available_tickets - 1})

        if rows_updated > 0:
            t = Ticket(
                ticket_number=f"TCK-CONCUR-{thread_idx}",
                event_id=event_id,
                user_id=user_id,
                status="CONFIRMED",
                price_paid=100.0
            )
            db.add(t)
            db.commit()
            success = True
        else:
            error_msg = "Sold out"
            db.rollback()
    except Exception as e:
        db.rollback()
        error_msg = str(e)
    finally:
        db.close()
    return {"thread_idx": thread_idx, "success": success, "error": error_msg}


def run_concurrency_test(num_threads=10):
    event_id = setup_test_db()
    
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(attempt_booking, event_id, 1, i) for i in range(num_threads)]
        for f in concurrent.futures.as_completed(futures):
            results.append(f.result())

    successes = [r for r in results if r["success"]]
    failures = [r for r in results if not r["success"]]

    db = TestingSessionLocal()
    final_event = db.query(Event).filter(Event.id == event_id).first()
    final_available = final_event.available_tickets
    total_tickets_created = db.query(Ticket).filter(Ticket.event_id == event_id).count()
    db.close()

    summary = {
        "total_attempted_threads": num_threads,
        "successful_bookings": len(successes),
        "failed_bookings": len(failures),
        "final_available_tickets": final_available,
        "total_tickets_in_db": total_tickets_created,
        "zero_double_booking_verified": bool(total_tickets_created == 3 and final_available == 0)
    }
    return summary

def test_concurrency_double_booking_prevention():
    summary = run_concurrency_test(num_threads=10)
    assert summary["successful_bookings"] == 3
    assert summary["failed_bookings"] == 7
    assert summary["final_available_tickets"] == 0
    assert summary["zero_double_booking_verified"] is True

if __name__ == "__main__":
    res = run_concurrency_test(num_threads=10)
    print("\n--- CONCURRENCY TEST RESULTS ---")
    for k, v in res.items():
        print(f"{k}: {v}")
