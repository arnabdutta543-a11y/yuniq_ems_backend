import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from admin.database import get_db
from admin import models, schemas
from admin.mail import send_recognition_email

router = APIRouter(prefix="/recognitions", tags=["Admin Recognitions"])

def _build_out(r: models.Recognition, db: Session) -> schemas.RecognitionOut:
    emp = db.query(models.Employee).filter(models.Employee.id == r.employee_id).first()
    giver = db.query(models.Employee).filter(models.Employee.id == r.given_by_id).first()
    return schemas.RecognitionOut(
        id=r.id, employee_id=r.employee_id, given_by_id=r.given_by_id,
        award_type=r.award_type, title=r.title, description=r.description,
        date=r.date, created_at=r.created_at,
        employee_name=emp.full_name if emp else "Unknown",
        given_by_name=giver.full_name if giver else "Unknown"
    )

@router.get("/", response_model=List[schemas.RecognitionOut])
def get_recognitions(
    given_by_id: Optional[str] = None,
    employee_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Recognition)
    if given_by_id:
        query = query.filter(models.Recognition.given_by_id == given_by_id)
    if employee_id:
        query = query.filter(models.Recognition.employee_id == employee_id)
    recs = query.order_by(models.Recognition.created_at.desc()).all()
    return [_build_out(r, db) for r in recs]

@router.post("/", response_model=schemas.RecognitionOut)
def create_recognition(
    rec_in: schemas.RecognitionCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    emp = db.query(models.Employee).filter(models.Employee.id == rec_in.employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    giver = db.query(models.Employee).filter(models.Employee.id == rec_in.given_by_id).first()
    if not giver:
        raise HTTPException(status_code=404, detail="Giver employee not found")

    rec_date = rec_in.date if rec_in.date else datetime.date.today()

    db_rec = models.Recognition(
        employee_id=rec_in.employee_id, given_by_id=rec_in.given_by_id,
        award_type=rec_in.award_type, title=rec_in.title,
        description=rec_in.description, date=rec_date
    )
    db.add(db_rec)

    notif = models.Notification(
        employee_id=rec_in.employee_id,
        title=f"🏆 Recognition: {rec_in.award_type}",
        message=f"{giver.full_name} has recognized you with '{rec_in.title}'. Keep up the great work!",
        read=False
    )
    db.add(notif)
    db.commit()
    db.refresh(db_rec)

    if emp and emp.email:
        background_tasks.add_task(
            send_recognition_email,
            to_email=emp.email, employee_name=emp.full_name,
            award_type=rec_in.award_type, title=rec_in.title,
            description=rec_in.description, given_by_name=giver.full_name
        )

    return _build_out(db_rec, db)

@router.delete("/{id}")
def delete_recognition(id: int, db: Session = Depends(get_db)):
    rec = db.query(models.Recognition).filter(models.Recognition.id == id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recognition not found")
    db.delete(rec)
    db.commit()
    return {"message": "Recognition deleted successfully"}
