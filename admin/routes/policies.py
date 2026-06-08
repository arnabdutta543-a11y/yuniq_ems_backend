import os
import shutil
import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
from admin.database import get_db
from admin import models, schemas

router = APIRouter(prefix="/policies", tags=["Admin Policies"])

# Static folder for uploaded PDFs — relative to backend/ root
STATIC_POLICIES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    "static",
    "policies"
)

@router.get("/", response_model=List[schemas.PolicyOut])
def get_policies(db: Session = Depends(get_db)):
    return db.query(models.Policy).order_by(models.Policy.published_at.desc()).all()

@router.post("/", response_model=schemas.PolicyOut)
def upload_policy(
    title: str = Form(...),
    category: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    os.makedirs(STATIC_POLICIES_DIR, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    safe_filename = f"{timestamp}_{file.filename.replace(' ', '_')}"
    file_path = os.path.join(STATIC_POLICIES_DIR, safe_filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    url_path = f"/static/policies/{safe_filename}"
    db_policy = models.Policy(
        title=title, category=category,
        url=url_path, published_at=datetime.date.today()
    )
    db.add(db_policy)
    db.commit()
    db.refresh(db_policy)
    return db_policy

@router.delete("/{id}")
def delete_policy(id: int, db: Session = Depends(get_db)):
    policy = db.query(models.Policy).filter(models.Policy.id == id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    if policy.url:
        filename = os.path.basename(policy.url)
        file_path = os.path.join(STATIC_POLICIES_DIR, filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Error removing file {file_path}: {e}")

    db.delete(policy)
    db.commit()
    return {"message": "Policy deleted successfully"}
