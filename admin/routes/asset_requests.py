from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from admin.database import get_db
from admin import models, schemas

router = APIRouter(prefix="/asset-requests", tags=["Admin Asset Requests"])

def _build_out(ar: models.AssetRequest, db: Session) -> schemas.AssetRequestOut:
    emp = db.query(models.Employee).filter(models.Employee.id == ar.employee_id).first()
    reviewer = None
    if ar.reviewed_by_id:
        reviewer = db.query(models.Employee).filter(models.Employee.id == ar.reviewed_by_id).first()
    return schemas.AssetRequestOut(
        id=ar.id, employee_id=ar.employee_id, item_name=ar.item_name,
        description=ar.description, priority=ar.priority, status=ar.status,
        it_response=ar.it_response, reviewed_by_id=ar.reviewed_by_id,
        created_at=ar.created_at, updated_at=ar.updated_at,
        employee_name=emp.full_name if emp else None,
        reviewed_by_name=reviewer.full_name if reviewer else None
    )

@router.get("/", response_model=List[schemas.AssetRequestOut])
def get_asset_requests(
    employee_id: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.AssetRequest)
    if employee_id:
        query = query.filter(models.AssetRequest.employee_id == employee_id)
    if status:
        query = query.filter(models.AssetRequest.status == status)
    requests = query.order_by(models.AssetRequest.created_at.desc()).all()
    return [_build_out(ar, db) for ar in requests]

@router.post("/", response_model=schemas.AssetRequestOut)
def create_asset_request(ar_in: schemas.AssetRequestCreate, db: Session = Depends(get_db)):
    emp = db.query(models.Employee).filter(models.Employee.id == ar_in.employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    db_ar = models.AssetRequest(
        employee_id=ar_in.employee_id, item_name=ar_in.item_name,
        description=ar_in.description, priority=ar_in.priority, status="Pending"
    )
    db.add(db_ar)
    db.commit()
    db.refresh(db_ar)
    return _build_out(db_ar, db)

@router.put("/{id}", response_model=schemas.AssetRequestOut)
def update_asset_request(id: int, ar_in: schemas.AssetRequestUpdate, db: Session = Depends(get_db)):
    db_ar = db.query(models.AssetRequest).filter(models.AssetRequest.id == id).first()
    if not db_ar:
        raise HTTPException(status_code=404, detail="Asset request not found")

    db_ar.status = ar_in.status
    if ar_in.it_response is not None:
        db_ar.it_response = ar_in.it_response
    if ar_in.reviewed_by_id is not None:
        db_ar.reviewed_by_id = ar_in.reviewed_by_id

    status_verb = "approved" if ar_in.status == "Approved" else "rejected"
    msg = f"Your asset request for '{db_ar.item_name}' has been {status_verb}."
    if ar_in.it_response:
        msg += f" IT note: {ar_in.it_response}"

    notif = models.Notification(
        employee_id=db_ar.employee_id,
        title=f"Asset Request {ar_in.status}",
        message=msg,
        read=False
    )
    db.add(notif)
    db.commit()
    db.refresh(db_ar)
    return _build_out(db_ar, db)

@router.delete("/{id}")
def delete_asset_request(id: int, db: Session = Depends(get_db)):
    db_ar = db.query(models.AssetRequest).filter(models.AssetRequest.id == id).first()
    if not db_ar:
        raise HTTPException(status_code=404, detail="Asset request not found")
    db.delete(db_ar)
    db.commit()
    return {"message": "Asset request deleted successfully"}
