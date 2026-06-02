from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from database import mock_db, get_db, TrainingDB
from routers.auth import get_current_user_id

router = APIRouter(prefix="/trainings", tags=["trainings"])

class EnrollRequest(BaseModel):
    course_name: str
    provider: str

class UpdateProgressRequest(BaseModel):
    course_id: int
    progress: float
    status: str # 'In Progress', 'Completed'

@router.get("/list")
def get_trainings(user_id: str = Depends(get_current_user_id), db = Depends(get_db)):
    if db:
        trainings = db.query(TrainingDB).filter(TrainingDB.user_id == user_id).all()
        # If database is connected, also query Certifications
        from database import CertificationDB
        certs = db.query(CertificationDB).filter(CertificationDB.user_id == user_id).all()
        return {
            "trainings": [{
                "id": t.id,
                "course_name": t.course_name,
                "provider": t.provider,
                "status": t.status,
                "progress": t.progress,
                "recommended_by_ai": t.recommended_by_ai
            } for t in trainings],
            "certifications": [{
                "id": c.id,
                "name": c.name,
                "authority": c.authority,
                "issued_date": c.issued_date.isoformat(),
                "expiry_date": c.expiry_date.isoformat() if c.expiry_date else None,
                "url": c.url
            } for c in certs]
        }
        
    # Mock fallback
    user_trainings = [t for t in mock_db.trainings if t["user_id"] == user_id]
    user_certs = [c for c in mock_db.certifications if c["user_id"] == user_id]
    return {
        "trainings": user_trainings,
        "certifications": user_certs
    }

@router.post("/enroll")
def enroll_training(data: EnrollRequest, user_id: str = Depends(get_current_user_id), db = Depends(get_db)):
    if db:
        # Check if already enrolled
        existing = db.query(TrainingDB).filter(
            TrainingDB.user_id == user_id, 
            TrainingDB.course_name == data.course_name
        ).first()
        if existing:
            if existing.status == 'Recommended':
                existing.status = 'In Progress'
                existing.progress = 0.0
                db.commit()
                return {"message": "Enrolled in recommended course", "course_id": existing.id}
            raise HTTPException(status_code=400, detail="Already enrolled in this course")
            
        new_training = TrainingDB(
            user_id=user_id,
            course_name=data.course_name,
            provider=data.provider,
            status="In Progress",
            progress=0.0,
            recommended_by_ai=False
        )
        db.add(new_training)
        db.commit()
        return {"message": "Enrolled successfully", "course_id": new_training.id}

    # Mock DB
    existing = next((t for t in mock_db.trainings if t["user_id"] == user_id and t["course_name"] == data.course_name), None)
    if existing:
        if existing["status"] == 'Recommended':
            existing["status"] = 'In Progress'
            existing["progress"] = 0.0
            return {"message": "Enrolled in recommended course"}
        raise HTTPException(status_code=400, detail="Already enrolled in this course")
        
    new_id = max([t["id"] for t in mock_db.trainings]) + 1 if mock_db.trainings else 1
    mock_db.trainings.append({
        "id": new_id,
        "user_id": user_id,
        "course_name": data.course_name,
        "provider": data.provider,
        "status": "In Progress",
        "progress": 0.0,
        "recommended_by_ai": False
    })
    return {"message": "Enrolled successfully"}

@router.post("/update")
def update_progress(data: UpdateProgressRequest, user_id: str = Depends(get_current_user_id), db = Depends(get_db)):
    if db:
        training = db.query(TrainingDB).filter(TrainingDB.id == data.course_id, TrainingDB.user_id == user_id).first()
        if not training:
            raise HTTPException(status_code=404, detail="Course not found")
        training.progress = data.progress
        training.status = data.status
        db.commit()
        return {"message": "Progress updated successfully"}

    # Mock DB
    training = next((t for t in mock_db.trainings if t["id"] == data.course_id and t["user_id"] == user_id), None)
    if not training:
        raise HTTPException(status_code=404, detail="Course not found")
    training["progress"] = data.progress
    training["status"] = data.status
    return {"message": "Progress updated successfully"}
