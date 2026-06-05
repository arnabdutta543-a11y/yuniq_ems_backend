from fastapi import APIRouter, Depends, HTTPException, status, Header, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from admin.database import get_db
from admin import models, schemas
from admin.mail import send_performance_review_email

router = APIRouter(prefix="/performance", tags=["Admin Performance"])

@router.get("/", response_model=List[schemas.PerformanceReviewOut])
def get_performance_reviews(db: Session = Depends(get_db)):
    return db.query(models.PerformanceReview).all()

@router.get("/employee/{employee_id}", response_model=List[schemas.PerformanceReviewOut])
def get_employee_reviews(employee_id: str, db: Session = Depends(get_db)):
    return db.query(models.PerformanceReview).filter(
        models.PerformanceReview.employee_id == employee_id
    ).all()

@router.post("/", response_model=schemas.PerformanceReviewOut)
def create_performance_review(
    review_in: schemas.PerformanceReviewCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    x_sender_name: Optional[str] = Header(None)
):
    emp = db.query(models.Employee).filter(models.Employee.id == review_in.employee_id).first()
    if not emp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    db_review = models.PerformanceReview(
        employee_id=review_in.employee_id, year=review_in.year,
        quality_rating=review_in.quality_rating,
        collaboration_rating=review_in.collaboration_rating,
        leadership_rating=review_in.leadership_rating,
        manager_comments=review_in.manager_comments
    )
    db.add(db_review)

    notif = models.Notification(
        employee_id=review_in.employee_id,
        title="Performance Review Logged",
        message=f"Your performance review for year {review_in.year} is now available in your portal.",
        read=False
    )
    db.add(notif)
    db.commit()
    db.refresh(db_review)

    if emp and emp.email:
        background_tasks.add_task(
            send_performance_review_email,
            to_email=emp.email, employee_name=emp.full_name,
            year=int(review_in.year),
            quality_rating=float(review_in.quality_rating),
            collaboration_rating=float(review_in.collaboration_rating),
            leadership_rating=float(review_in.leadership_rating),
            comments=review_in.manager_comments, sender_name=x_sender_name
        )

    return db_review

@router.put("/{id}", response_model=schemas.PerformanceReviewOut)
def update_performance_review(id: int, review_in: schemas.PerformanceReviewUpdate, db: Session = Depends(get_db)):
    db_review = db.query(models.PerformanceReview).filter(models.PerformanceReview.id == id).first()
    if not db_review:
        raise HTTPException(status_code=404, detail="Performance evaluation not found.")

    update_data = review_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_review, field, value)

    db.commit()
    db.refresh(db_review)
    return db_review

@router.delete("/{id}")
def delete_performance_review(id: int, db: Session = Depends(get_db)):
    db_review = db.query(models.PerformanceReview).filter(models.PerformanceReview.id == id).first()
    if not db_review:
        raise HTTPException(status_code=404, detail="Performance evaluation not found.")
    db.delete(db_review)
    db.commit()
    return {"message": "Performance evaluation deleted successfully."}
