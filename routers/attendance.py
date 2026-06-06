from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
import datetime
from database import mock_db, get_db, AttendanceLogDB, NotificationDB
from routers.auth import get_current_user_id
from pydantic import BaseModel


router = APIRouter(prefix="/attendance", tags=["attendance"])

@router.get("/status")
def get_attendance_status(user_id: str = Depends(get_current_user_id), db = Depends(get_db)):
    today = datetime.date.today()
    today_str = today.isoformat()
    
    if db:
        # Check if currently punched in (log exists for today with null punch_out_at)
        active_log = db.query(AttendanceLogDB).filter(
            AttendanceLogDB.user_id == user_id,
            AttendanceLogDB.date == today,
            AttendanceLogDB.punch_out_at == None
        ).first()
        
        # Get all completed logs for today
        completed_logs = db.query(AttendanceLogDB).filter(
            AttendanceLogDB.user_id == user_id,
            AttendanceLogDB.date == today,
            AttendanceLogDB.punch_out_at != None
        ).all()
        
        total_hours = sum(log.total_hours for log in completed_logs)
        activity_log = []
        
        # Merge activities
        for log in completed_logs:
            activity_log.extend(log.activity_log or [])
        if active_log:
            activity_log.extend(active_log.activity_log or [])
            
        # If currently punched in, calculate elapsed hours
        is_punched_in = active_log is not None
        last_punch_in = active_log.punch_in_at if active_log else None
        
        if active_log:
            p_in = datetime.datetime.fromisoformat(active_log.punch_in_at.replace("Z", "+00:00"))
            now = datetime.datetime.now(datetime.timezone.utc)
            elapsed = (now - p_in).total_seconds() / 3600.0
            total_hours += elapsed
            
        status = "Office"
        for act in activity_log:
            if isinstance(act, dict) and act.get("action") == "WFH":
                status = "WFH"
                break
            
        return {
            "date": today_str,
            "is_punched_in": is_punched_in,
            "last_punch_in": last_punch_in,
            "total_hours": round(total_hours, 2),
            "activity_log": activity_log,
            "status": status
        }
        
    # Fallback to mock DB
    punch_in_time = mock_db.active_punches.get(user_id)
    today_log = next((log for log in mock_db.attendance_logs 
                      if log["user_id"] == user_id and log["date"] == today_str), None)
                      
    activity_log = today_log["activity_log"] if today_log else []
    total_hours = today_log["total_hours"] if today_log else 0.0
    
    if punch_in_time:
        p_in = datetime.datetime.fromisoformat(punch_in_time.replace("Z", "+00:00"))
        now = datetime.datetime.now(datetime.timezone.utc)
        elapsed = (now - p_in).total_seconds() / 3600.0
        total_hours += elapsed
        
    status = "Office"
    for act in activity_log:
        if isinstance(act, dict) and act.get("action") == "WFH":
            status = "WFH"
            break
        
    return {
        "date": today_str,
        "is_punched_in": punch_in_time is not None,
        "last_punch_in": punch_in_time,
        "total_hours": round(total_hours, 2),
        "activity_log": activity_log,
        "status": status
    }

@router.post("/punch-in")
def punch_in(user_id: str = Depends(get_current_user_id), db = Depends(get_db)):
    now_str = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
    today = datetime.date.today()
    
    if db:
        # Check if already punched in
        active_log = db.query(AttendanceLogDB).filter(
            AttendanceLogDB.user_id == user_id,
            AttendanceLogDB.date == today,
            AttendanceLogDB.punch_out_at == None
        ).first()
        
        if active_log:
            raise HTTPException(status_code=400, detail="Already punched in")
            
        # Create new active log
        new_log = AttendanceLogDB(
            id=f"att-{int(datetime.datetime.now().timestamp())}",
            user_id=user_id,
            date=today,
            punch_in_at=now_str,
            punch_out_at=None,
            total_hours=0.0,
            activity_log=[{"time": now_str, "action": "Punch-In"}]
        )
        
        from sqlalchemy.exc import IntegrityError
        try:
            db.add(new_log)
            # Add Notification
            new_notif = NotificationDB(
                id=f"notif-{int(datetime.datetime.now().timestamp())}",
                user_id=user_id,
                title="Punched In",
                message=f"You punched in successfully at {datetime.datetime.now().strftime('%H:%M:%S')}.",
                read=False,
                created_at=now_str
            )
            db.add(new_notif)
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=400, detail="Active attendance session already exists for today")
            
        return {"message": "Punched in successfully", "time": now_str}
        
    # Fallback to mock DB
    if user_id in mock_db.active_punches:
        raise HTTPException(status_code=400, detail="Already punched in")
    mock_db.active_punches[user_id] = now_str
    today_str = today.isoformat()
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
def punch_out(user_id: str = Depends(get_current_user_id), db = Depends(get_db)):
    now_str = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
    today = datetime.date.today()
    
    if db:
        # Get active punch log
        active_log = db.query(AttendanceLogDB).filter(
            AttendanceLogDB.user_id == user_id,
            AttendanceLogDB.date == today,
            AttendanceLogDB.punch_out_at == None
        ).first()
        
        if not active_log:
            raise HTTPException(status_code=400, detail="Not punched in")
            
        p_in = datetime.datetime.fromisoformat(active_log.punch_in_at.replace("Z", "+00:00"))
        p_out = datetime.datetime.fromisoformat(now_str.replace("Z", "+00:00"))
        elapsed_hours = (p_out - p_in).total_seconds() / 3600.0
        
        active_log.punch_out_at = now_str
        active_log.total_hours = round(elapsed_hours, 2)
        # SQLAlchemy mutability warning workaround: assign new list to trigger update
        updated_log = list(active_log.activity_log or [])
        updated_log.append({"time": now_str, "action": "Punch-Out"})
        active_log.activity_log = updated_log
        
        # Add Notification
        new_notif = NotificationDB(
            id=f"notif-{int(datetime.datetime.now().timestamp())}",
            user_id=user_id,
            title="Punched Out",
            message=f"You punched out successfully at {datetime.datetime.now().strftime('%H:%M:%S')}. Duration: {round(elapsed_hours, 2)} hrs.",
            read=False,
            created_at=now_str
        )
        db.add(new_notif)
        db.commit()
        return {"message": "Punched out successfully", "time": now_str, "session_hours": round(elapsed_hours, 2)}
        
    # Fallback to mock DB
    punch_in_time = mock_db.active_punches.pop(user_id, None)
    if not punch_in_time:
        raise HTTPException(status_code=400, detail="Not punched in")
    today_str = today.isoformat()
    p_in = datetime.datetime.fromisoformat(punch_in_time.replace("Z", "+00:00"))
    p_out = datetime.datetime.fromisoformat(now_str.replace("Z", "+00:00"))
    elapsed_hours = (p_out - p_in).total_seconds() / 3600.0
    
    today_log = next((log for log in mock_db.attendance_logs 
                      if log["user_id"] == user_id and log["date"] == today_str), None)
    if today_log:
        today_log["punch_out_at"] = now_str
        today_log["total_hours"] = round(today_log["total_hours"] + elapsed_hours, 2)
        today_log["activity_log"].append({"time": now_str, "action": "Punch-Out"})
    mock_db.notifications.append({
        "id": f"notif-{len(mock_db.notifications) + 1}",
        "user_id": user_id,
        "title": "Punched Out",
        "message": f"You punched out successfully at {datetime.datetime.now().strftime('%H:%M:%S')}. Session duration: {round(elapsed_hours, 2)} hrs.",
        "read": False,
        "created_at": now_str
    })
    return {"message": "Punched out successfully", "time": now_str, "session_hours": round(elapsed_hours, 2)}

class WFHPayload(BaseModel):
    date: str
    reason: str

@router.post("/wfh")
def log_wfh(payload: WFHPayload, user_id: str = Depends(get_current_user_id), db = Depends(get_db)):
    try:
        target_date = datetime.date.fromisoformat(payload.date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
        
    now_str = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
    
    if db:
        # Check if WFH or any attendance is already logged for this user on this date
        existing_logs = db.query(AttendanceLogDB).filter(
            AttendanceLogDB.user_id == user_id,
            AttendanceLogDB.date == target_date
        ).all()
        
        for log in existing_logs:
            if log.activity_log:
                for act in log.activity_log:
                    if isinstance(act, dict) and act.get("action") == "WFH":
                        raise HTTPException(status_code=400, detail="WFH already logged for this date")
        
        wfh_log = AttendanceLogDB(
            user_id=user_id,
            date=target_date,
            punch_in_at=payload.date + "T09:00:00Z",
            punch_out_at=payload.date + "T17:00:00Z",
            total_hours=8.0,
            activity_log=[{"time": now_str, "action": "WFH", "reason": payload.reason}]
        )
        db.add(wfh_log)
        
        # Add Notification
        new_notif = NotificationDB(
            id=f"notif-{int(datetime.datetime.now().timestamp())}",
            user_id=user_id,
            title="WFH Logged",
            message=f"WFH schedule logged successfully for {payload.date}.",
            read=False,
            created_at=now_str
        )
        db.add(new_notif)
        db.commit()
        return {"message": "WFH logged successfully"}
        
    # Fallback to mock DB
    existing_logs = [log for log in mock_db.attendance_logs if log["user_id"] == user_id and log["date"] == payload.date]
    for log in existing_logs:
        for act in log.get("activity_log", []):
            if act.get("action") == "WFH":
                raise HTTPException(status_code=400, detail="WFH already logged for this date")
                
    wfh_log = {
        "id": f"att-{len(mock_db.attendance_logs) + 1}",
        "user_id": user_id,
        "date": payload.date,
        "punch_in_at": payload.date + "T09:00:00Z",
        "punch_out_at": payload.date + "T17:00:00Z",
        "total_hours": 8.0,
        "activity_log": [{"time": now_str, "action": "WFH", "reason": payload.reason}]
    }
    mock_db.attendance_logs.append(wfh_log)
    mock_db.notifications.append({
        "id": f"notif-{len(mock_db.notifications) + 1}",
        "user_id": user_id,
        "title": "WFH Logged",
        "message": f"WFH schedule logged successfully for {payload.date}.",
        "read": False,
        "created_at": now_str
    })
    return {"message": "WFH logged successfully"}

@router.get("/statistics")
def get_attendance_statistics(user_id: str = Depends(get_current_user_id), db = Depends(get_db)):
    today = datetime.date.today()
    start_of_week = today - datetime.timedelta(days=today.weekday())
    start_of_month = today.replace(day=1)
    
    if db:
        logs = db.query(AttendanceLogDB).filter(AttendanceLogDB.user_id == user_id).all()
        today_hours = 0.0
        week_hours = 0.0
        month_hours = 0.0
        
        for log in logs:
            if log.date == today:
                today_hours += log.total_hours
            if log.date >= start_of_week:
                week_hours += log.total_hours
            if log.date >= start_of_month:
                month_hours += log.total_hours
                
        # Include current active punch duration if active
        active = db.query(AttendanceLogDB).filter(
            AttendanceLogDB.user_id == user_id,
            AttendanceLogDB.date == today,
            AttendanceLogDB.punch_out_at == None
        ).first()
        
        if active:
            p_in = datetime.datetime.fromisoformat(active.punch_in_at.replace("Z", "+00:00"))
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
        
    # Fallback to mock DB
    user_logs = [log for log in mock_db.attendance_logs if log["user_id"] == user_id]
    today_hours = 0.0
    week_hours = 0.0
    month_hours = 0.0
    today_str = today.isoformat()
    
    for log in user_logs:
        log_date = datetime.date.fromisoformat(log["date"])
        hours = log["total_hours"]
        if log["date"] == today_str:
            today_hours += hours
        if log_date >= start_of_week:
            week_hours += hours
        if log_date >= start_of_month:
            month_hours += hours
            
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

@router.get("/history")
def get_attendance_history(user_id: str = Depends(get_current_user_id), db = Depends(get_db)):
    if db:
        logs = db.query(AttendanceLogDB).filter(
            AttendanceLogDB.user_id == user_id
        ).order_by(AttendanceLogDB.date.desc()).limit(30).all()
        
        res = []
        for log in logs:
            status = "Office"
            if log.activity_log:
                for act in log.activity_log:
                    if isinstance(act, dict) and act.get("action") == "WFH":
                        status = "WFH"
                        break
            res.append({
                "id": log.id,
                "date": log.date.isoformat(),
                "punch_in_at": log.punch_in_at,
                "punch_out_at": log.punch_out_at,
                "total_hours": float(log.total_hours),
                "status": status
            })
        return res
        
    # Fallback to mock DB
    user_logs = [log for log in mock_db.attendance_logs if log["user_id"] == user_id]
    user_logs = sorted(user_logs, key=lambda x: x["date"], reverse=True)[:30]
    res = []
    for log in user_logs:
        status = "Office"
        for act in log.get("activity_log", []):
            if act.get("action") == "WFH":
                status = "WFH"
                break
        res.append({
            **log,
            "status": status
        })
    return res
