from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import datetime
from database import mock_db, get_db, AssetDB, NotificationDB, ProfileDB, AssetRequestDB
from routers.auth import get_current_user_id

router = APIRouter(prefix="/assets", tags=["assets"])

class ReturnRequest(BaseModel):
    asset_id: int

class CreateAssetRequest(BaseModel):
    request_type: str
    description: str

class AssetRequestAction(BaseModel):
    action: str # Approved, Rejected, In Review, Completed
    admin_notes: Optional[str] = None

@router.get("/list")
def get_assets(user_id: str = Depends(get_current_user_id), db = Depends(get_db)):
    if db:
        assets = db.query(AssetDB).filter(AssetDB.user_id == user_id).all()
        return [{
            "id": a.id,
            "user_id": a.user_id,
            "asset_name": a.asset_name,
            "serial_number": a.serial_number,
            "assigned_date": a.assigned_date.isoformat(),
            "status": a.status
        } for a in assets]
        
    return [a for a in mock_db.assets if a["user_id"] == user_id]

@router.post("/return")
def request_asset_return(data: ReturnRequest, user_id: str = Depends(get_current_user_id), db = Depends(get_db)):
    now_str = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
    
    if db:
        asset = db.query(AssetDB).filter(AssetDB.id == data.asset_id, AssetDB.user_id == user_id).first()
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found or not assigned to you")
            
        asset.status = "Return Requested"
        
        # Log notification
        new_notif = NotificationDB(
            id=f"notif-{int(datetime.datetime.now().timestamp())}",
            user_id=user_id,
            title="Asset Return Requested",
            message=f"Return request for asset '{asset.asset_name}' (S/N: {asset.serial_number}) has been initiated.",
            read=False,
            created_at=now_str
        )
        db.add(new_notif)
        db.commit()
        return {"message": "Return request initiated successfully"}
        
    # Mock fallback
    asset = next((a for a in mock_db.assets if a["id"] == data.asset_id and a["user_id"] == user_id), None)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found or not assigned to you")
        
    asset["status"] = "Return Requested"
    
    mock_db.notifications.append({
        "id": f"notif-{len(mock_db.notifications) + 1}",
        "user_id": user_id,
        "title": "Asset Return Requested",
        "message": f"Return request for asset '{asset['asset_name']}' (S/N: {asset['serial_number']}) has been initiated.",
        "read": False,
        "created_at": now_str
    })
    return {"message": "Return request initiated successfully"}

from typing import Optional

@router.post("/request")
def raise_asset_request(data: CreateAssetRequest, user_id: str = Depends(get_current_user_id), db = Depends(get_db)):
    now_str = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
    if db:
        new_req = AssetRequestDB(
            user_id=user_id,
            request_type=data.request_type,
            description=data.description,
            status="Submitted",
            created_at=datetime.datetime.now()
        )
        db.add(new_req)
        db.commit()
        db.refresh(new_req)
        
        # Log notification
        new_notif = NotificationDB(
            id=f"notif-{int(datetime.datetime.now().timestamp())}",
            user_id=user_id,
            title="IT Support Request Submitted",
            message=f"Your request for '{data.request_type}' has been submitted successfully.",
            read=False,
            created_at=now_str
        )
        db.add(new_notif)
        db.commit()
        return {"message": "IT request raised successfully", "id": new_req.id}
        
    return {"message": "Mock success"}

@router.get("/requests")
def get_user_asset_requests(user_id: str = Depends(get_current_user_id), db = Depends(get_db)):
    if db:
        requests = db.query(AssetRequestDB).filter(AssetRequestDB.user_id == user_id).order_by(AssetRequestDB.created_at.desc()).all()
        return [{
            "id": r.id,
            "user_id": r.user_id,
            "request_type": r.request_type,
            "description": r.description,
            "status": r.status,
            "created_at": r.created_at.isoformat() if hasattr(r.created_at, 'isoformat') else str(r.created_at),
            "admin_notes": r.admin_notes
        } for r in requests]
    return []

@router.get("/admin/requests")
def get_all_asset_requests(db = Depends(get_db)):
    if db:
        requests = db.query(AssetRequestDB).order_by(AssetRequestDB.created_at.desc()).all()
        return [{
            "id": r.id,
            "user_id": r.user_id,
            "employee_name": db.query(ProfileDB).filter(ProfileDB.id == r.user_id).first().full_name if db.query(ProfileDB).filter(ProfileDB.id == r.user_id).first() else r.user_id,
            "request_type": r.request_type,
            "description": r.description,
            "status": r.status,
            "created_at": r.created_at.isoformat() if hasattr(r.created_at, 'isoformat') else str(r.created_at),
            "admin_notes": r.admin_notes
        } for r in requests]
    return []

@router.post("/request/{request_id}/action")
def action_asset_request(request_id: int, data: AssetRequestAction, db = Depends(get_db)):
    now_str = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
    if db:
        req = db.query(AssetRequestDB).filter(AssetRequestDB.id == request_id).first()
        if not req:
            raise HTTPException(status_code=404, detail="Request not found")
        
        req.status = data.action
        if data.admin_notes is not None:
            req.admin_notes = data.admin_notes
            
        # Log notification to employee
        new_notif = NotificationDB(
            id=f"notif-{int(datetime.datetime.now().timestamp())}",
            user_id=req.user_id,
            title=f"IT Request Update: {data.action}",
            message=f"Your request for '{req.request_type}' is updated to '{data.action}'. Notes: {data.admin_notes or 'None'}",
            read=False,
            created_at=now_str
        )
        db.add(new_notif)
        db.commit()
        return {"message": f"IT request status updated to {data.action}"}
        
    return {"message": "Mock success"}
