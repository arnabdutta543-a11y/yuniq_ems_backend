from fastapi import APIRouter, Depends, HTTPException, Header, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from admin.database import get_db
from admin import models, schemas
from admin.mail import send_travel_status_email

router = APIRouter(prefix="/travel", tags=["Admin Travel"])

@router.get("/", response_model=List[schemas.TravelRequestOut])
def get_travel_requests(db: Session = Depends(get_db)):
    reqs = db.query(models.TravelRequest).order_by(models.TravelRequest.departure_date.desc()).all()
    results = []
    for r in reqs:
        emp = db.query(models.Employee).filter(models.Employee.id == r.employee_id).first()
        results.append(schemas.TravelRequestOut(
            id=r.id, employee_id=r.employee_id,
            employee_name=emp.full_name if emp else "Unknown",
            destination=r.destination, departure_date=r.departure_date,
            return_date=r.return_date, status=r.status,
            selected_flight=r.selected_flight, selected_hotel=r.selected_hotel
        ))
    return results

@router.post("/{id}/approve")
def approve_travel(
    id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    x_sender_name: Optional[str] = Header(None)
):
    req = db.query(models.TravelRequest).filter(models.TravelRequest.id == id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Travel request not found")

    req.status = "Approved"

    notif = models.Notification(
        employee_id=req.employee_id,
        title="Travel Request Approved",
        message=f"Your travel request to {req.destination} starting {req.departure_date} has been Approved.",
        read=False
    )
    db.add(notif)
    db.commit()

    emp = db.query(models.Employee).filter(models.Employee.id == req.employee_id).first()
    if emp and emp.email:
        background_tasks.add_task(
            send_travel_status_email,
            to_email=emp.email, employee_name=emp.full_name,
            destination=req.destination, departure_date=str(req.departure_date),
            return_date=str(req.return_date), status="Approved", sender_name=x_sender_name
        )

    return {"message": "Travel request approved successfully"}

@router.post("/{id}/reject")
def reject_travel(
    id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    x_sender_name: Optional[str] = Header(None)
):
    req = db.query(models.TravelRequest).filter(models.TravelRequest.id == id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Travel request not found")

    req.status = "Rejected"

    notif = models.Notification(
        employee_id=req.employee_id,
        title="Travel Request Rejected",
        message=f"Your travel request to {req.destination} starting {req.departure_date} has been Rejected.",
        read=False
    )
    db.add(notif)
    db.commit()

    emp = db.query(models.Employee).filter(models.Employee.id == req.employee_id).first()
    if emp and emp.email:
        background_tasks.add_task(
            send_travel_status_email,
            to_email=emp.email, employee_name=emp.full_name,
            destination=req.destination, departure_date=str(req.departure_date),
            return_date=str(req.return_date), status="Rejected", sender_name=x_sender_name
        )

    return {"message": "Travel request rejected successfully"}
