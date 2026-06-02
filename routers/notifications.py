from fastapi import APIRouter, HTTPException, Depends
from database import mock_db
from routers.auth import get_current_user_id

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.get("/list")
def get_notifications(user_id: str = Depends(get_current_user_id)):
    """
    Get in-app notifications for the user.
    """
    notifs = [n for n in mock_db.notifications if n["user_id"] == user_id]
    # Sort by created_at descending
    notifs.sort(key=lambda x: x["created_at"], reverse=True)
    return notifs

@router.post("/read/{notif_id}")
def mark_notification_as_read(notif_id: str, user_id: str = Depends(get_current_user_id)):
    """
    Mark a notification as read.
    """
    notif = next((n for n in mock_db.notifications if n["id"] == notif_id and n["user_id"] == user_id), None)
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    notif["read"] = True
    return {"message": "Notification marked as read", "notification": notif}
