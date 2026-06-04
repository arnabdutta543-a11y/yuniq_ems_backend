from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Any
import datetime
from database import get_db, OkrDB, ProfileDB
from routers.auth import get_current_user_id

router = APIRouter(prefix="/okrs", tags=["okrs"])

class OkrSaveRequest(BaseModel):
    id: Optional[int] = None
    type: str
    objective: str
    key_results: List[Any]
    progress: float
    year: int
    quarter: int
    due_date: Optional[str] = None
    success_criteria: Optional[str] = None
    assigned_by: Optional[str] = None
    user_id: Optional[str] = None

class OkrProgressRequest(BaseModel):
    progress: float
    evidence_url: Optional[str] = None
    completion_remarks: Optional[str] = None

class OkrAppraisalRequest(BaseModel):
    appraisal_summary: str
    appraisal_evidence: Optional[str] = None

def serialize_okr(o: OkrDB, db) -> dict:
    assigned_by_name = "System"
    employee_name = ""
    if db:
        if o.assigned_by:
            creator = db.query(ProfileDB).filter(ProfileDB.id == o.assigned_by).first()
            if creator:
                assigned_by_name = creator.full_name
        emp = db.query(ProfileDB).filter(ProfileDB.id == o.user_id).first()
        if emp:
            employee_name = emp.full_name
    return {
        "id": o.id,
        "user_id": o.user_id,
        "employee_name": employee_name,
        "type": o.type,
        "objective": o.objective,
        "key_results": o.key_results,
        "progress": o.progress,
        "year": o.year,
        "quarter": o.quarter,
        "due_date": o.due_date.isoformat() if o.due_date else None,
        "success_criteria": o.success_criteria,
        "assigned_by": o.assigned_by,
        "assigned_by_name": assigned_by_name,
        "evidence_url": o.evidence_url,
        "completion_remarks": o.completion_remarks,
        "appraisal_submitted": o.appraisal_submitted,
        "appraisal_summary": o.appraisal_summary,
        "appraisal_evidence": o.appraisal_evidence
    }

@router.get("/list")
def get_okrs(user_id: str = Depends(get_current_user_id), db = Depends(get_db)):
    if db:
        okrs = db.query(OkrDB).filter(OkrDB.user_id == user_id).order_by(OkrDB.year.desc(), OkrDB.quarter.desc()).all()
        return [serialize_okr(o, db) for o in okrs]
    return []

@router.get("/all")
def get_all_okrs(user_id: str = Depends(get_current_user_id), db = Depends(get_db)):
    """
    Get all OKRs in the organization (HR Manager/Director scope).
    """
    if db:
        # Check permissions
        curr_user = db.query(ProfileDB).filter(ProfileDB.id == user_id).first()
        if not curr_user or curr_user.role not in ["HR Manager", "Director", "Manager"]:
            raise HTTPException(status_code=403, detail="You do not have permission to view all OKRs")
            
        okrs = db.query(OkrDB).order_by(OkrDB.user_id, OkrDB.year.desc()).all()
        return [serialize_okr(o, db) for o in okrs]
    return []

@router.post("/assign")
def assign_okr(data: OkrSaveRequest, user_id: str = Depends(get_current_user_id), db = Depends(get_db)):
    """
    Allows HR or Reporting Manager to assign goals to employees.
    """
    if db:
        curr_user = db.query(ProfileDB).filter(ProfileDB.id == user_id).first()
        if not curr_user or curr_user.role not in ["HR Manager", "Director", "Manager"]:
            raise HTTPException(status_code=403, detail="Only HR or Managers can assign goals.")
            
        target_user_id = data.user_id if data.user_id else user_id
        due_d = datetime.date.fromisoformat(data.due_date) if data.due_date else None
        
        okr_record = OkrDB(
            user_id=target_user_id,
            type=data.type,
            objective=data.objective,
            key_results=data.key_results,
            progress=data.progress,
            year=data.year,
            quarter=data.quarter,
            due_date=due_d,
            success_criteria=data.success_criteria,
            assigned_by=user_id
        )
        db.add(okr_record)
        db.commit()
        db.refresh(okr_record)
        return {"message": "Goal assigned successfully", "okr": serialize_okr(okr_record, db)}
    return {"message": "Goal assigned successfully"}

@router.post("/save")
def save_okr(data: OkrSaveRequest, user_id: str = Depends(get_current_user_id), db = Depends(get_db)):
    if db:
        due_d = datetime.date.fromisoformat(data.due_date) if data.due_date else None
        if data.id:
            okr_record = db.query(OkrDB).filter(OkrDB.id == data.id, OkrDB.user_id == user_id).first()
            if not okr_record:
                raise HTTPException(status_code=404, detail="OKR not found")
            okr_record.type = data.type
            okr_record.objective = data.objective
            okr_record.key_results = data.key_results
            okr_record.progress = data.progress
            okr_record.year = data.year
            okr_record.quarter = data.quarter
            okr_record.due_date = due_d
            okr_record.success_criteria = data.success_criteria
        else:
            okr_record = OkrDB(
                user_id=user_id,
                type=data.type,
                objective=data.objective,
                key_results=data.key_results,
                progress=data.progress,
                year=data.year,
                quarter=data.quarter,
                due_date=due_d,
                success_criteria=data.success_criteria,
                assigned_by=user_id
            )
            db.add(okr_record)
        db.commit()
        return {"message": "OKR saved successfully"}
    return {"message": "OKR saved successfully"}

@router.post("/{okr_id}/progress")
def update_okr_progress(okr_id: int, data: OkrProgressRequest, user_id: str = Depends(get_current_user_id), db = Depends(get_db)):
    if db:
        okr_record = db.query(OkrDB).filter(OkrDB.id == okr_id, OkrDB.user_id == user_id).first()
        if not okr_record:
            raise HTTPException(status_code=404, detail="OKR not found")
            
        okr_record.progress = data.progress
        if data.evidence_url is not None:
            okr_record.evidence_url = data.evidence_url
        if data.completion_remarks is not None:
            okr_record.completion_remarks = data.completion_remarks
            
        db.commit()
        db.refresh(okr_record)
        return {"message": "OKR progress updated", "okr": serialize_okr(okr_record, db)}
    return {"message": "OKR progress updated"}

@router.post("/{okr_id}/appraisal")
def submit_okr_appraisal(okr_id: int, data: OkrAppraisalRequest, user_id: str = Depends(get_current_user_id), db = Depends(get_db)):
    if db:
        okr_record = db.query(OkrDB).filter(OkrDB.id == okr_id, OkrDB.user_id == user_id).first()
        if not okr_record:
            raise HTTPException(status_code=404, detail="OKR not found")
            
        okr_record.appraisal_submitted = True
        okr_record.appraisal_summary = data.appraisal_summary
        if data.appraisal_evidence is not None:
            okr_record.appraisal_evidence = data.appraisal_evidence
            
        db.commit()
        db.refresh(okr_record)
        return {"message": "Appraisal preparation submitted", "okr": serialize_okr(okr_record, db)}
    return {"message": "Appraisal preparation submitted"}
