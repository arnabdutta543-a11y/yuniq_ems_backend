from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import datetime
from database import mock_db, get_db, RecognitionDB, NotificationDB
from routers.auth import get_current_user_id

router = APIRouter(prefix="/recognitions", tags=["recognitions"])

class RecognitionGiveRequest(BaseModel):
    user_id: str # recipient user ID
    award_type: str # 'Spot Award', 'Peer Appreciation', etc.
    title: str
    description: str

@router.get("/list")
def get_recognitions(db = Depends(get_db)):
    if db:
        recs = db.query(RecognitionDB).order_by(RecognitionDB.date.desc()).all()
        return [{
            "id": r.id,
            "user_id": r.user_id,
            "award_type": r.award_type,
            "title": r.title,
            "description": r.description,
            "given_by": r.given_by,
            "date": r.date.isoformat()
        } for r in recs]
        
    return mock_db.recognitions

@router.post("/give")
def give_recognition(data: RecognitionGiveRequest, user_id: str = Depends(get_current_user_id), db = Depends(get_db)):
    # Find the sender's full name
    giver_name = "Someone"
    recipient_id = data.user_id
    
    if db:
        from database import ProfileDB
        giver_p = db.query(ProfileDB).filter(ProfileDB.id == user_id).first()
        if giver_p:
            giver_name = giver_p.full_name
            
        rec_record = RecognitionDB(
            user_id=recipient_id,
            award_type=data.award_type,
            title=data.title,
            description=data.description,
            given_by=giver_name,
            date=datetime.date.today()
        )
        db.add(rec_record)
        
        # Notify the recipient
        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
        new_notif = NotificationDB(
            id=f"notif-{int(datetime.datetime.now().timestamp())}",
            user_id=recipient_id,
            title=f"New Recognition: {data.award_type}",
            message=f"You received a {data.award_type} from {giver_name}: '{data.title}'",
            read=False,
            created_at=now_str
        )
        db.add(new_notif)
        db.commit()
        return {"message": "Recognition given successfully"}
        
    # Mock fallback
    giver = next((p for p in mock_db.profiles if p["id"] == user_id), None)
    if giver:
        giver_name = giver["full_name"]
        
    new_id = max([r["id"] for r in mock_db.recognitions]) + 1 if mock_db.recognitions else 1
    mock_db.recognitions.append({
        "id": new_id,
        "user_id": recipient_id,
        "award_type": data.award_type,
        "title": data.title,
        "description": data.description,
        "given_by": giver_name,
        "date": datetime.date.today().isoformat()
    })
    
    now_str = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
    mock_db.notifications.append({
        "id": f"notif-{len(mock_db.notifications) + 1}",
        "user_id": recipient_id,
        "title": f"New Recognition: {data.award_type}",
        "message": f"You received a {data.award_type} from {giver_name}: '{data.title}'",
        "read": False,
        "created_at": now_str
    })
    
    return {"message": "Recognition given successfully"}
