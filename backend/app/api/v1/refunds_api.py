from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.authorization import get_current_user, require_roles
from app.models.user import User
from app.models.ticket import Ticket, Event
from app.models.refund import RefundRequest, RefundPolicy
from app.schemas.schemas import RefundCreateRequest, RefundReviewRequest
from app.services.refund_service import calculate_refund_amount, approve_refund

router = APIRouter()

@router.post("/refunds/request")
def request_refund(req: RefundCreateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == req.ticket_id, Ticket.user_id == current_user.id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found or not owned by user")

    if ticket.status in ["REFUNDED", "USED", "TRANSFERRED"]:
        raise HTTPException(status_code=400, detail=f"Cannot request refund for ticket with status '{ticket.status}'")

    existing = db.query(RefundRequest).filter(RefundRequest.ticket_id == ticket.id, RefundRequest.status == "REQUESTED").first()
    if existing:
        raise HTTPException(status_code=400, detail="Refund request already submitted and pending review")

    event = db.query(Event).filter(Event.id == ticket.event_id).first()
    eligible_amount, policy_note = calculate_refund_amount(db, ticket, event)

    refund_req = RefundRequest(
        ticket_id=ticket.id,
        user_id=current_user.id,
        event_id=ticket.event_id,
        quantity_refunded=req.quantity_refunded or 1,
        amount_requested=ticket.price_paid,
        amount_approved=eligible_amount,
        reason=req.reason or policy_note,
        status="REQUESTED" if eligible_amount > 0 else "REJECTED",
        rejection_reason=None if eligible_amount > 0 else policy_note
    )

    db.add(refund_req)
    db.commit()
    db.refresh(refund_req)

    return {
        "refund_id": refund_req.id,
        "eligible_amount": eligible_amount,
        "policy_note": policy_note,
        "status": refund_req.status
    }

@router.get("/refunds/my-requests")
def list_my_refund_requests(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    requests = db.query(RefundRequest).filter(RefundRequest.user_id == current_user.id).all()
    return requests

@router.get("/organizer/refunds")
def list_organizer_refund_requests(current_user: User = Depends(require_roles(["organizer", "admin"])), db: Session = Depends(get_db)):
    if current_user.role in ["super_admin", "admin"]:
        requests = db.query(RefundRequest).all()
    else:
        organizer_event_ids = [e.id for e in db.query(Event).filter(Event.organizer_id == current_user.id).all()]
        requests = db.query(RefundRequest).filter(RefundRequest.event_id.in_(organizer_event_ids)).all()
    return requests

@router.post("/organizer/refunds/{refund_id}/review")
def review_refund_request(refund_id: int, review: RefundReviewRequest, current_user: User = Depends(require_roles(["organizer", "admin"])), db: Session = Depends(get_db)):
    refund_req = db.query(RefundRequest).filter(RefundRequest.id == refund_id).first()
    if not refund_req:
        raise HTTPException(status_code=404, detail="Refund request not found")

    if review.status == "APPROVED":
        approve_refund(db, refund_req, current_user.id)
    else:
        refund_req.status = "REJECTED"
        refund_req.rejection_reason = review.rejection_reason or "Rejected by organizer"
        refund_req.reviewed_by_user_id = current_user.id
        db.commit()

    return {"message": f"Refund request #{refund_id} updated to {refund_req.status}"}
