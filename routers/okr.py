from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Any
from database import mock_db, get_db, OkrDB
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

@router.get("/list")
def get_okrs(user_id: str = Depends(get_current_user_id), db = Depends(get_db)):
    if db:
        okrs = db.query(OkrDB).filter(OkrDB.user_id == user_id).all()
        return [{
            "id": o.id,
            "user_id": o.user_id,
            "type": o.type,
            "objective": o.objective,
            "key_results": o.key_results,
            "progress": o.progress,
            "year": o.year,
            "quarter": o.quarter
        } for o in okrs]
        
    return [o for o in mock_db.okrs if o["user_id"] == user_id]

@router.post("/save")
def save_okr(data: OkrSaveRequest, user_id: str = Depends(get_current_user_id), db = Depends(get_db)):
    if db:
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
        else:
            okr_record = OkrDB(
                user_id=user_id,
                type=data.type,
                objective=data.objective,
                key_results=data.key_results,
                progress=data.progress,
                year=data.year,
                quarter=data.quarter
            )
            db.add(okr_record)
        db.commit()
        return {"message": "OKR saved successfully"}

    # Mock DB fallback
    if data.id:
        okr = next((o for o in mock_db.okrs if o["id"] == data.id and o["user_id"] == user_id), None)
        if not okr:
            raise HTTPException(status_code=404, detail="OKR not found")
        okr.update({
            "type": data.type,
            "objective": data.objective,
            "key_results": data.key_results,
            "progress": data.progress,
            "year": data.year,
            "quarter": data.quarter
        })
    else:
        new_id = max([o["id"] for o in mock_db.okrs]) + 1 if mock_db.okrs else 1
        mock_db.okrs.append({
            "id": new_id,
            "user_id": user_id,
            "type": data.type,
            "objective": data.objective,
            "key_results": data.key_results,
            "progress": data.progress,
            "year": data.year,
            "quarter": data.quarter
        })
    return {"message": "OKR saved successfully"}
