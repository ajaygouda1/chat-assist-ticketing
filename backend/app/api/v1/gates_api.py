from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.core.database import get_db
from app.core.authorization import get_current_user
from app.models.user import User
from app.models.gate import Gate
from app.models.ticket import Ticket, ScanLog

router = APIRouter()

@router.get("/events/{event_id}/gates")
def list_event_gates(event_id: int, db: Session = Depends(get_db)):
    gates = db.query(Gate).filter(Gate.event_id == event_id).all()
    if not gates:
        # Default gates
        g1 = Gate(event_id=event_id, name="Gate A - Main Entrance")
        g2 = Gate(event_id=event_id, name="Gate B - VIP & Staff Entrance")
        db.add_all([g1, g2])
        db.commit()
        gates = [g1, g2]
    return gates

@router.post("/tickets/scan/batch-sync")
def batch_sync_offline_scans(payload: List[Dict[str, Any]], current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Reconciles queued scan logs captured offline during network dropouts.
    Detects duplicate scans safely and records reconciliation results.
    """
    results = []
    for item in payload:
        ticket_number = item.get("ticket_number")
        gate_id = item.get("gate_id")
        
        ticket = db.query(Ticket).filter(Ticket.ticket_number == ticket_number).first()
        if not ticket:
            res = "INVALID"
        elif ticket.status == "USED":
            res = "RECONCILED_DUPLICATE"
        elif ticket.status == "CONFIRMED":
            ticket.status = "USED"
            res = "VALID"
        else:
            res = f"REJECTED_{ticket.status}"

        log = ScanLog(
            ticket_id=ticket.id if ticket else None,
            ticket_number=ticket_number,
            event_id=ticket.event_id if ticket else None,
            staff_id=f"STAFF-USER-{current_user.id}",
            gate_id=gate_id,
            result=res,
            offline_sync=True
        )
        db.add(log)
        results.append({"ticket_number": ticket_number, "reconciliation_result": res})

    db.commit()
    return {"synced_count": len(results), "details": results}
