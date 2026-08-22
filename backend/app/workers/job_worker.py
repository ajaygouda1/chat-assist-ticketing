import time
from datetime import datetime, timedelta
from app.core.database import SessionLocal
from app.models.seating import Seat
from app.models.waitlist import WaitlistEntry
from app.models.failed_jobs import FailedJob
from app.core.logger import logger

def run_background_tasks():
    """
    Executes background worker cycle for seat hold cleanup, waitlist processing, and reminders.
    """
    db = SessionLocal()
    try:
        now = datetime.utcnow()

        # Task 1: Clean expired seat holds
        expired_seats = db.query(Seat).filter(
            Seat.status == "HELD",
            Seat.held_until < now
        ).all()

        for s in expired_seats:
            s.status = "AVAILABLE"
            s.held_by_user_id = None
            s.held_until = None
        db.commit()

        if expired_seats:
            logger.info(f"Released {len(expired_seats)} expired seat holds")

        # Task 2: Clean expired waitlist notifications
        expired_waitlists = db.query(WaitlistEntry).filter(
            WaitlistEntry.status == "NOTIFIED",
            WaitlistEntry.purchase_deadline < now
        ).all()

        for w in expired_waitlists:
            w.status = "EXPIRED"
        db.commit()

    except Exception as e:
        logger.error(f"Background worker error: {str(e)}")
        # Log to Dead-Letter FailedJobs
        fj = FailedJob(
            job_type="BACKGROUND_WORKER_CYCLE",
            entity_id="CRON_WORKER",
            last_error=str(e),
            status="FAILED"
        )
        db.add(fj)
        db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("Starting ChatAssist Background Worker Daemon...")
    while True:
        run_background_tasks()
        time.sleep(15)  # Run worker cycle every 15 seconds
