from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import datetime
from database import mock_db, get_db, AssetDB, NotificationDB
from routers.auth import get_current_user_id

router = APIRouter(prefix="/assets", tags=["assets"])

class ReturnRequest(BaseModel):
    asset_id: int

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
