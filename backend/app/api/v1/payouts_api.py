from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.authorization import get_current_user, require_roles
from app.models.user import User
from app.models.ticket import Ticket, Event
from app.models.refund import RefundRequest
from app.models.payout_ledger import PayoutLedger

router = APIRouter()

@router.get("/organizer/events/{event_id}/payout-ledger")
def get_event_payout_ledger(event_id: int, current_user: User = Depends(require_roles(["organizer", "admin"])), db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    tickets = db.query(Ticket).filter(Ticket.event_id == event_id, Ticket.status != "CANCELLED").all()
    gross_sales = sum([t.price_paid for t in tickets])

    refunds = db.query(RefundRequest).filter(RefundRequest.event_id == event_id, RefundRequest.status == "REFUNDED").all()
    refunds_total = sum([r.amount_approved for r in refunds])

    # Platform fee = 5%, Payment processing fee = 2%
    net_sales = max(0.0, gross_sales - refunds_total)
    platform_fee = round(net_sales * 0.05, 2)
    payment_processing_fee = round(net_sales * 0.02, 2)
    organizer_net = round(net_sales - platform_fee - payment_processing_fee, 2)

    ledger = db.query(PayoutLedger).filter(PayoutLedger.event_id == event_id).first()
    if not ledger:
        ledger = PayoutLedger(
            organizer_id=event.organizer_id or current_user.id,
            event_id=event_id,
            gross_sales=gross_sales,
            refunds_total=refunds_total,
            platform_fee=platform_fee,
            payment_processing_fee=payment_processing_fee,
            net_payout=organizer_net,
            status="PENDING"
        )
        db.add(ledger)
    else:
        ledger.gross_sales = gross_sales
        ledger.refunds_total = refunds_total
        ledger.platform_fee = platform_fee
        ledger.payment_processing_fee = payment_processing_fee
        ledger.net_payout = organizer_net
    db.commit()

    return {
        "event_id": event_id,
        "gross_sales": gross_sales,
        "refunds_total": refunds_total,
        "platform_fee": platform_fee,
        "payment_processing_fee": payment_processing_fee,
        "organizer_net": organizer_net,
        "status": ledger.status
    }
