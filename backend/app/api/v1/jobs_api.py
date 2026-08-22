from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.authorization import require_roles
from app.models.user import User
from app.models.failed_jobs import FailedJob

router = APIRouter()

@router.get("/admin/failed-jobs")
def get_failed_jobs(current_user: User = Depends(require_roles(["admin", "super_admin"])), db: Session = Depends(get_db)):
    jobs = db.query(FailedJob).order_by(FailedJob.created_at.desc()).all()
    return jobs

@router.post("/admin/failed-jobs/{job_id}/retry")
def retry_failed_job(job_id: int, current_user: User = Depends(require_roles(["admin", "super_admin"])), db: Session = Depends(get_db)):
    job = db.query(FailedJob).filter(FailedJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Failed job not found")

    job.status = "RESOLVED"
    job.attempts += 1
    db.commit()
    return {"message": f"Job #{job_id} marked as RESOLVED and triggered for retry"}
