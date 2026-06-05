from fastapi import APIRouter, HTTPException, Depends
from database import mock_db, get_db, NotificationDB
from routers.auth import get_current_user_id

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.get("/list")
def get_notifications(user_id: str = Depends(get_current_user_id), db = Depends(get_db)):
    if db:
        notifs_records = db.query(NotificationDB).filter(
            NotificationDB.user_id == user_id
        ).order_by(NotificationDB.created_at.desc()).all()
        
        return [{
            "id": n.id,
            "user_id": n.user_id,
            "title": n.title,
            "message": n.message,
            "read": n.read,
            "created_at": n.created_at
        } for n in notifs_records]
        
    # Fallback to mock DB
    notifs = [n for n in mock_db.notifications if n["user_id"] == user_id]
    notifs.sort(key=lambda x: x["created_at"], reverse=True)
    return notifs

@router.post("/read/{notif_id}")
def mark_notification_as_read(notif_id: str, user_id: str = Depends(get_current_user_id), db = Depends(get_db)):
    if db:
        notif_record = db.query(NotificationDB).filter(
            NotificationDB.id == notif_id,
            NotificationDB.user_id == user_id
        ).first()
        
        if not notif_record:
            raise HTTPException(status_code=404, detail="Notification not found")
        notif_record.read = True
        db.commit()
        return {"message": "Notification marked as read"}
        
    # Fallback to mock DB
    notif = next((n for n in mock_db.notifications if n["id"] == notif_id and n["user_id"] == user_id), None)
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    notif["read"] = True
    return {"message": "Notification marked as read", "notification": notif}

@router.post("/read-all")
def mark_all_notifications_as_read(user_id: str = Depends(get_current_user_id), db = Depends(get_db)):
    if db:
        db.query(NotificationDB).filter(
            NotificationDB.user_id == user_id,
            NotificationDB.read == False
        ).update({NotificationDB.read: True}, synchronize_session=False)
        db.commit()
        return {"message": "All notifications marked as read"}
        
    # Fallback to mock DB
    for n in mock_db.notifications:
        if n["user_id"] == user_id:
            n["read"] = True
    return {"message": "All notifications marked as read"}
