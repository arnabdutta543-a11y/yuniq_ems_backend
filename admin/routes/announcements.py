import datetime
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from admin.database import get_db
from admin import models, schemas
from admin.mail import send_announcement_email

router = APIRouter(prefix="/announcements", tags=["Admin Announcements"])

@router.get("/", response_model=List[schemas.AnnouncementOut])
def get_announcements(db: Session = Depends(get_db)):
    return db.query(models.Announcement).order_by(models.Announcement.created_at.desc()).all()

@router.post("/", response_model=schemas.AnnouncementOut)
def create_announcement(
    ann_in: schemas.AnnouncementCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    db_ann = models.Announcement(
        title=ann_in.title,
        content=ann_in.content,
        category=ann_in.category,
        created_at=datetime.date.today()
    )
    db.add(db_ann)
    db.flush()

    employees = db.query(models.Employee).all()

    for emp in employees:
        notif = models.Notification(
            employee_id=emp.id,
            title=f"📢 Announcement: {ann_in.title}",
            message=ann_in.content[:200] + ("..." if len(ann_in.content) > 200 else ""),
            read=False,
            created_at=datetime.datetime.utcnow()
        )
        db.add(notif)

        if emp.email:
            background_tasks.add_task(
                send_announcement_email,
                to_email=emp.email,
                employee_name=emp.full_name,
                title=ann_in.title,
                category=ann_in.category,
                content=ann_in.content
            )

    db.commit()
    db.refresh(db_ann)
    return db_ann
