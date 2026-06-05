from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from admin.database import get_db
from admin import models, schemas

router = APIRouter(prefix="/trainings", tags=["Admin Trainings"])

def _build_out(t: models.Training, db: Session) -> schemas.TrainingOut:
    emp = db.query(models.Employee).filter(models.Employee.id == t.employee_id).first()
    return schemas.TrainingOut(
        id=t.id, employee_id=t.employee_id, course_name=t.course_name,
        provider=t.provider, status=t.status, progress=t.progress,
        completion_date=t.completion_date, recommended_by_ai=t.recommended_by_ai,
        notes=t.notes, created_at=t.created_at,
        employee_name=emp.full_name if emp else None
    )

@router.get("/", response_model=List[schemas.TrainingOut])
def get_trainings(
    employee_id: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Training)
    if employee_id:
        query = query.filter(models.Training.employee_id == employee_id)
    if status:
        query = query.filter(models.Training.status == status)
    trainings = query.order_by(models.Training.created_at.desc()).all()
    return [_build_out(t, db) for t in trainings]

@router.post("/", response_model=schemas.TrainingOut)
def create_training(t_in: schemas.TrainingCreate, db: Session = Depends(get_db)):
    emp = db.query(models.Employee).filter(models.Employee.id == t_in.employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    db_t = models.Training(
        employee_id=t_in.employee_id, course_name=t_in.course_name,
        provider=t_in.provider, status=t_in.status, progress=t_in.progress,
        completion_date=t_in.completion_date, recommended_by_ai=t_in.recommended_by_ai,
        notes=t_in.notes
    )
    db.add(db_t)

    notif = models.Notification(
        employee_id=t_in.employee_id,
        title="📚 New Training Assigned",
        message=f"You have been enrolled in '{t_in.course_name}'" + (f" by {t_in.provider}." if t_in.provider else "."),
        read=False
    )
    db.add(notif)
    db.commit()
    db.refresh(db_t)
    return _build_out(db_t, db)

@router.put("/{id}", response_model=schemas.TrainingOut)
def update_training(id: int, t_in: schemas.TrainingUpdate, db: Session = Depends(get_db)):
    db_t = db.query(models.Training).filter(models.Training.id == id).first()
    if not db_t:
        raise HTTPException(status_code=404, detail="Training record not found")

    update_data = t_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_t, field, value)

    if db_t.progress == 100 and db_t.status != "Completed":
        import datetime
        db_t.status = "Completed"
        if not db_t.completion_date:
            db_t.completion_date = datetime.date.today()

    db.commit()
    db.refresh(db_t)
    return _build_out(db_t, db)

@router.delete("/{id}")
def delete_training(id: int, db: Session = Depends(get_db)):
    db_t = db.query(models.Training).filter(models.Training.id == id).first()
    if not db_t:
        raise HTTPException(status_code=404, detail="Training record not found")
    db.delete(db_t)
    db.commit()
    return {"message": "Training record deleted successfully"}
