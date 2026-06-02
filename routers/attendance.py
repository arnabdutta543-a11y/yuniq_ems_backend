from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
import datetime
from database import mock_db
from routers.auth import get_current_user_id

router = APIRouter(prefix="/attendance", tags=["attendance"])

@router.get("/status")
def get_attendance_status(user_id: str = Depends(get_current_user_id)):
    """
    Get today's punch status and logs.
    """
    today_str = datetime.date.today().isoformat()
    
    # Check if there is an active punch-in
    punch_in_time = mock_db.active_punches.get(user_id)
    
    # Get today's completed log if any
    today_log = next((log for log in mock_db.attendance_logs 
                      if log["user_id"] == user_id and log["date"] == today_str), None)
                      
    activity_log = today_log["activity_log"] if today_log else []
    total_hours = today_log["total_hours"] if today_log else 0.0
    
    # If currently punched in, calculate hours dynamically
    if punch_in_time:
        p_in = datetime.datetime.fromisoformat(punch_in_time.replace("Z", "+00:00"))
        now = datetime.datetime.now(datetime.timezone.utc)
        elapsed = (now - p_in).total_seconds() / 3600.0
        total_hours += elapsed
        
    return {
        "date": today_str,
        "is_punched_in": punch_in_time is not None,
        "last_punch_in": punch_in_time,
        "total_hours": round(total_hours, 2),
        "activity_log": activity_log
    }

@router.post("/punch-in")
def punch_in(user_id: str = Depends(get_current_user_id)):
    if user_id in mock_db.active_punches:
        raise HTTPException(status_code=400, detail="Already punched in")
        
    now_str = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
    mock_db.active_punches[user_id] = now_str
    
    # Find or create today's log in mock_db
    today_str = datetime.date.today().isoformat()
    today_log = next((log for log in mock_db.attendance_logs 
                      if log["user_id"] == user_id and log["date"] == today_str), None)
                      
    if not today_log:
        today_log = {
            "id": f"att-{len(mock_db.attendance_logs) + 1}",
            "user_id": user_id,
            "date": today_str,
            "punch_in_at": now_str,
            "punch_out_at": None,
            "total_hours": 0.0,
            "activity_log": []
        }
        mock_db.attendance_logs.append(today_log)
        
    today_log["activity_log"].append({"time": now_str, "action": "Punch-In"})
    
    # Create an in-app notification
    mock_db.notifications.append({
        "id": f"notif-{len(mock_db.notifications) + 1}",
        "user_id": user_id,
        "title": "Punched In",
        "message": f"You punched in successfully at {datetime.datetime.now().strftime('%H:%M:%S')}.",
        "read": False,
        "created_at": now_str
    })
    
    return {"message": "Punched in successfully", "time": now_str}

@router.post("/punch-out")
def punch_out(user_id: str = Depends(get_current_user_id)):
    punch_in_time = mock_db.active_punches.pop(user_id, None)
    if not punch_in_time:
        raise HTTPException(status_code=400, detail="Not punched in")
        
    now_str = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
    today_str = datetime.date.today().isoformat()
    
    # Calculate hours worked this session
    p_in = datetime.datetime.fromisoformat(punch_in_time.replace("Z", "+00:00"))
    p_out = datetime.datetime.fromisoformat(now_str.replace("Z", "+00:00"))
    elapsed_hours = (p_out - p_in).total_seconds() / 3600.0
    
    # Update log
    today_log = next((log for log in mock_db.attendance_logs 
                      if log["user_id"] == user_id and log["date"] == today_str), None)
                      
    if today_log:
        today_log["punch_out_at"] = now_str
        today_log["total_hours"] = round(today_log["total_hours"] + elapsed_hours, 2)
        today_log["activity_log"].append({"time": now_str, "action": "Punch-Out"})
    
    # Create notification
    mock_db.notifications.append({
        "id": f"notif-{len(mock_db.notifications) + 1}",
        "user_id": user_id,
        "title": "Punched Out",
        "message": f"You punched out successfully at {datetime.datetime.now().strftime('%H:%M:%S')}. Session duration: {round(elapsed_hours, 2)} hrs.",
        "read": False,
        "created_at": now_str
    })
    
    return {"message": "Punched out successfully", "time": now_str, "session_hours": round(elapsed_hours, 2)}

@router.get("/statistics")
def get_attendance_statistics(user_id: str = Depends(get_current_user_id)):
    """
    Get weekly and monthly aggregated hours.
    """
    # Filter logs for user
    user_logs = [log for log in mock_db.attendance_logs if log["user_id"] == user_id]
    
    # Calculate stats
    today_hours = 0.0
    week_hours = 0.0
    month_hours = 0.0
    
    today = datetime.date.today()
    start_of_week = today - datetime.timedelta(days=today.weekday())
    start_of_month = today.replace(day=1)
    
    for log in user_logs:
        log_date = datetime.date.fromisoformat(log["date"])
        hours = log["total_hours"]
        
        if log_date == today:
            today_hours += hours
        if log_date >= start_of_week:
            week_hours += hours
        if log_date >= start_of_month:
            month_hours += hours
            
    # Add active punch-in duration if applicable
    punch_in_time = mock_db.active_punches.get(user_id)
    if punch_in_time:
        p_in = datetime.datetime.fromisoformat(punch_in_time.replace("Z", "+00:00"))
        now = datetime.datetime.now(datetime.timezone.utc)
        elapsed = (now - p_in).total_seconds() / 3600.0
        
        today_hours += elapsed
        week_hours += elapsed
        month_hours += elapsed
        
    return {
        "today": round(today_hours, 2),
        "this_week": round(week_hours, 2),
        "this_month": round(month_hours, 2)
    }
