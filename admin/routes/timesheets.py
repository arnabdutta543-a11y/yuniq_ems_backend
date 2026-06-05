from fastapi import APIRouter, Depends, HTTPException, Header, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from admin.database import get_db
from admin import models, schemas
from admin.mail import send_timesheet_status_email

router = APIRouter(prefix="/timesheets", tags=["Admin Timesheets"])

@router.get("/", response_model=List[schemas.TimesheetOut])
def get_timesheets(db: Session = Depends(get_db)):
    timesheets = db.query(models.Timesheet).order_by(models.Timesheet.week_start.desc()).all()
    results = []
    for ts in timesheets:
        emp = db.query(models.Employee).filter(models.Employee.id == ts.employee_id).first()
        entries_out = [
            schemas.TimesheetEntryOut(
                id=e.id, timesheet_id=e.timesheet_id, date=e.date,
                project=e.project, hours=e.hours, description=e.description
            ) for e in ts.entries
        ]
        results.append(schemas.TimesheetOut(
            id=ts.id, employee_id=ts.employee_id,
            employee_name=emp.full_name if emp else "Unknown",
            week_start=ts.week_start, status=ts.status, entries=entries_out
        ))
    return results

@router.get("/pending", response_model=List[schemas.TimesheetOut])
def get_pending_timesheets(db: Session = Depends(get_db)):
    timesheets = db.query(models.Timesheet).filter(
        models.Timesheet.status == "Submitted"
    ).order_by(models.Timesheet.week_start.asc()).all()
    results = []
    for ts in timesheets:
        emp = db.query(models.Employee).filter(models.Employee.id == ts.employee_id).first()
        entries_out = [
            schemas.TimesheetEntryOut(
                id=e.id, timesheet_id=e.timesheet_id, date=e.date,
                project=e.project, hours=e.hours, description=e.description
            ) for e in ts.entries
        ]
        results.append(schemas.TimesheetOut(
            id=ts.id, employee_id=ts.employee_id,
            employee_name=emp.full_name if emp else "Unknown",
            week_start=ts.week_start, status=ts.status, entries=entries_out
        ))
    return results

@router.post("/{id}/approve")
def approve_timesheet(
    id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    x_sender_name: Optional[str] = Header(None)
):
    ts = db.query(models.Timesheet).filter(models.Timesheet.id == id).first()
    if not ts:
        raise HTTPException(status_code=404, detail="Timesheet not found")

    ts.status = "Approved"

    notif = models.Notification(
        employee_id=ts.employee_id,
        title="Timesheet Approved",
        message=f"Your timesheet for week starting {ts.week_start} has been Approved.",
        read=False
    )
    db.add(notif)
    db.commit()

    emp = db.query(models.Employee).filter(models.Employee.id == ts.employee_id).first()
    if emp and emp.email:
        background_tasks.add_task(
            send_timesheet_status_email,
            to_email=emp.email, employee_name=emp.full_name,
            week_start=str(ts.week_start), status="Approved", sender_name=x_sender_name
        )

    return {"message": "Timesheet approved successfully"}

@router.post("/{id}/reject")
def reject_timesheet(
    id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    x_sender_name: Optional[str] = Header(None)
):
    ts = db.query(models.Timesheet).filter(models.Timesheet.id == id).first()
    if not ts:
        raise HTTPException(status_code=404, detail="Timesheet not found")

    ts.status = "Rejected"

    notif = models.Notification(
        employee_id=ts.employee_id,
        title="Timesheet Rejected",
        message=f"Your timesheet for week starting {ts.week_start} has been Rejected. Please edit and resubmit.",
        read=False
    )
    db.add(notif)
    db.commit()

    emp = db.query(models.Employee).filter(models.Employee.id == ts.employee_id).first()
    if emp and emp.email:
        background_tasks.add_task(
            send_timesheet_status_email,
            to_email=emp.email, employee_name=emp.full_name,
            week_start=str(ts.week_start), status="Rejected", sender_name=x_sender_name
        )

    return {"message": "Timesheet rejected successfully"}
