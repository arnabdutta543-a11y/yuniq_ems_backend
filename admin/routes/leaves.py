from fastapi import APIRouter, Depends, HTTPException, Header, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from admin.database import get_db
from admin import models, schemas
from admin.mail import send_leave_status_email

router = APIRouter(prefix="/leaves", tags=["Admin Leaves"])

@router.get("/", response_model=List[schemas.LeaveOut])
def get_leaves(db: Session = Depends(get_db)):
    leaves = db.query(models.Leave).order_by(models.Leave.from_date.desc()).all()
    results = []
    for l in leaves:
        emp = db.query(models.Employee).filter(models.Employee.id == l.employee_id).first()
        results.append(schemas.LeaveOut(
            id=l.id, employee_id=l.employee_id,
            employee_name=emp.full_name if emp else "Unknown",
            leave_type=l.leave_type, from_date=l.from_date, to_date=l.to_date,
            num_days=l.num_days, reason=l.reason, status=l.status,
            applied_date=l.applied_date, recalled=l.recalled
        ))
    return results

@router.get("/pending", response_model=List[schemas.LeaveOut])
def get_pending_leaves(db: Session = Depends(get_db)):
    leaves = db.query(models.Leave).filter(
        models.Leave.status == "Pending"
    ).order_by(models.Leave.from_date.asc()).all()
    results = []
    for l in leaves:
        emp = db.query(models.Employee).filter(models.Employee.id == l.employee_id).first()
        results.append(schemas.LeaveOut(
            id=l.id, employee_id=l.employee_id,
            employee_name=emp.full_name if emp else "Unknown",
            leave_type=l.leave_type, from_date=l.from_date, to_date=l.to_date,
            num_days=l.num_days, reason=l.reason, status=l.status,
            applied_date=l.applied_date, recalled=l.recalled
        ))
    return results

@router.post("/{id}/approve")
def approve_leave(
    id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    x_sender_name: Optional[str] = Header(None)
):
    leave = db.query(models.Leave).filter(models.Leave.id == id).first()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")

    leave.status = "Approved"

    emp = db.query(models.Employee).filter(models.Employee.id == leave.employee_id).first()
    if emp:
        num_days = int(float(leave.num_days))
        current_balance = emp.leave_balance if emp.leave_balance is not None else 0
        new_balance = current_balance - num_days
        if new_balance < 0:
            emp.lop_days = (emp.lop_days or 0) + abs(new_balance)
            emp.leave_balance = 0
        else:
            emp.leave_balance = new_balance

    notif = models.Notification(
        employee_id=leave.employee_id,
        title="Leave Approved",
        message=f"Your leave request for {leave.from_date} has been Approved by the Admin.",
        read=False
    )
    db.add(notif)
    db.commit()

    if emp and emp.email:
        background_tasks.add_task(
            send_leave_status_email,
            to_email=emp.email, employee_name=emp.full_name,
            leave_type=leave.leave_type, from_date=str(leave.from_date),
            to_date=str(leave.to_date), num_days=float(leave.num_days),
            reason=leave.reason, status="Approved", sender_name=x_sender_name
        )

    return {"message": "Leave request approved successfully"}

@router.post("/{id}/reject")
def reject_leave(
    id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    x_sender_name: Optional[str] = Header(None)
):
    leave = db.query(models.Leave).filter(models.Leave.id == id).first()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")

    leave.status = "Rejected"

    notif = models.Notification(
        employee_id=leave.employee_id,
        title="Leave Rejected",
        message=f"Your leave request for {leave.from_date} has been Rejected by the Admin.",
        read=False
    )
    db.add(notif)
    db.commit()

    emp = db.query(models.Employee).filter(models.Employee.id == leave.employee_id).first()
    if emp and emp.email:
        background_tasks.add_task(
            send_leave_status_email,
            to_email=emp.email, employee_name=emp.full_name,
            leave_type=leave.leave_type, from_date=str(leave.from_date),
            to_date=str(leave.to_date), num_days=float(leave.num_days),
            reason=leave.reason, status="Rejected", sender_name=x_sender_name
        )

    return {"message": "Leave request rejected successfully"}
