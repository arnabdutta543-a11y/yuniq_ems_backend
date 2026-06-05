from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import datetime
from database import mock_db, get_db, LeaveDB, ProfileDB, NotificationDB
from routers.auth import get_current_user_id
from email_notifier import send_email_notification

router = APIRouter(prefix="/leave", tags=["leave"])

class ApplyLeaveRequest(BaseModel):
    leave_type: str
    from_date: str # YYYY-MM-DD
    to_date: str # YYYY-MM-DD
    num_days: float
    reason: str
    is_half_day: Optional[bool] = False
    half_day_session: Optional[str] = None
    attachments: Optional[str] = "[]"

def serialize_leave(l: LeaveDB) -> dict:
    import json
    try:
        attachments_list = json.loads(l.attachments) if l.attachments else []
    except Exception:
        attachments_list = []
    return {
        "id": l.id,
        "user_id": l.user_id,
        "leave_type": l.leave_type,
        "from_date": l.from_date.isoformat(),
        "to_date": l.to_date.isoformat(),
        "num_days": l.num_days,
        "reason": l.reason,
        "status": l.status,
        "applied_date": l.applied_date.isoformat(),
        "recalled": l.recalled,
        "is_half_day": l.is_half_day,
        "half_day_session": l.half_day_session,
        "attachments": attachments_list
    }

@router.get("/my-leaves")
def get_my_leaves(user_id: str = Depends(get_current_user_id), db = Depends(get_db)):
    if db:
        leaves_records = db.query(LeaveDB).filter(LeaveDB.user_id == user_id).order_by(LeaveDB.from_date.desc()).all()
        return [serialize_leave(l) for l in leaves_records]
        
    return []

@router.get("/balance")
def get_leave_balance(user_id: str = Depends(get_current_user_id), db = Depends(get_db)):
    if db:
        emp = db.query(ProfileDB).filter(ProfileDB.id == user_id).first()
        if emp:
            taken = emp.paid_leaves - emp.leave_balance
            return {
                "balance": float(emp.leave_balance),
                "taken": float(taken),
                "lop": float(emp.lop_days),
                "paid_leaves": float(emp.paid_leaves),
                "leave_year": emp.leave_year
            }
        
    return {
        "balance": 24.0,
        "taken": 8.0,
        "lop": 0.0,
        "paid_leaves": 24.0,
        "leave_year": 2026
    }

@router.get("/calculate-days")
def calculate_days(
    from_date: str,
    to_date: str,
    is_half_day: bool = False,
    half_day_session: str = None,
    user_id: str = Depends(get_current_user_id),
    db = Depends(get_db)
):
    try:
        from_d = datetime.date.fromisoformat(from_date)
        to_d = datetime.date.fromisoformat(to_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format (use YYYY-MM-DD)")
        
    if from_d > to_d:
        return {"num_days": 0.0}
        
    if db:
        emp = db.query(ProfileDB).filter(ProfileDB.id == user_id).first()
        office = emp.office if emp else "All"
        if not office:
            office = "All"
            
        from database import HolidayDB
        holidays = db.query(HolidayDB).filter(
            HolidayDB.date >= from_d,
            HolidayDB.date <= to_d,
            (HolidayDB.location == 'All') | (HolidayDB.location.ilike(office))
        ).all()
        holiday_dates = {h.date for h in holidays}
        
        days_count = 0.0
        curr = from_d
        while curr <= to_d:
            if curr.weekday() not in (5, 6) and curr not in holiday_dates:
                days_count += 1.0
            curr += datetime.timedelta(days=1)
            
        if is_half_day:
            days_count = 0.5 if days_count > 0 else 0.0
            
        return {"num_days": days_count}
        
    return {"num_days": 1.0}

@router.post("/apply")
def apply_leave(data: ApplyLeaveRequest, user_id: str = Depends(get_current_user_id), db = Depends(get_db)):
    try:
        from_d = datetime.date.fromisoformat(data.from_date)
        to_d = datetime.date.fromisoformat(data.to_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format (use YYYY-MM-DD)")
        
    if from_d > to_d:
        raise HTTPException(status_code=400, detail="From date cannot be after To date")
        
    now_str = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
    
    if db:
        # Calculate working days
        emp = db.query(ProfileDB).filter(ProfileDB.id == user_id).first()
        office = emp.office if emp else "All"
        if not office:
            office = "All"
            
        from database import HolidayDB
        holidays = db.query(HolidayDB).filter(
            HolidayDB.date >= from_d,
            HolidayDB.date <= to_d,
            (HolidayDB.location == 'All') | (HolidayDB.location.ilike(office))
        ).all()
        holiday_dates = {h.date for h in holidays}
        
        days_count = 0.0
        curr = from_d
        while curr <= to_d:
            if curr.weekday() not in (5, 6) and curr not in holiday_dates:
                days_count += 1.0
            curr += datetime.timedelta(days=1)
            
        if data.is_half_day:
            days_count = 0.5 if days_count > 0 else 0.0
            
        new_leave = LeaveDB(
            user_id=user_id,
            leave_type=data.leave_type,
            from_date=from_d,
            to_date=to_d,
            num_days=days_count,
            reason=data.reason,
            status="Pending",
            applied_date=datetime.date.today(),
            recalled=False,
            is_half_day=data.is_half_day,
            half_day_session=data.half_day_session if data.is_half_day else None,
            attachments=data.attachments
        )
        db.add(new_leave)
        
        # Add notification
        new_notif = NotificationDB(
            id=f"notif-{int(datetime.datetime.now().timestamp())}",
            user_id=user_id,
            title="Leave Applied",
            message=f"Your leave request for {data.from_date} has been submitted for approval.",
            read=False,
            created_at=now_str
        )
        db.add(new_notif)
        db.commit()
        db.refresh(new_leave)
        
        # Send mail notification
        profile = db.query(ProfileDB).filter(ProfileDB.id == user_id).first()
        if profile and profile.manager_id:
            manager = db.query(ProfileDB).filter(ProfileDB.id == profile.manager_id).first()
            if manager:
                send_email_notification(
                    to_email=manager.email,
                    subject=f"Leave Application: {profile.full_name}",
                    body_html=f"<p>{profile.full_name} has applied for leave from {data.from_date} to {data.to_date}. Reason: {data.reason}</p>",
                    body_text=f"{profile.full_name} applied for leave from {data.from_date} to {data.to_date}.\nReason: {data.reason}"
                )
        return {"message": "Leave applied successfully", "leave": serialize_leave(new_leave)}
        
    return {"message": "Leave applied successfully"}

@router.post("/recall/{leave_id}")
def recall_leave(leave_id: int, user_id: str = Depends(get_current_user_id), db = Depends(get_db)):
    now_str = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
    
    if db:
        leave_record = db.query(LeaveDB).filter(LeaveDB.id == leave_id, LeaveDB.user_id == user_id).first()
        if not leave_record:
            raise HTTPException(status_code=404, detail="Leave request not found")
        
        leave_record.status = "Recalled"
        leave_record.recalled = True
        
        # Notification
        new_notif = NotificationDB(
            id=f"notif-{int(datetime.datetime.now().timestamp())}",
            user_id=user_id,
            title="Leave Recalled",
            message=f"Your leave request starting {leave_record.from_date} was successfully recalled.",
            read=False,
            created_at=now_str
        )
        db.add(new_notif)
        db.commit()
        return {"message": "Leave recalled successfully"}
        
    # Fallback to mock DB
    leave = next((l for l in mock_db.leaves if l["id"] == leave_id and l["user_id"] == user_id), None)
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")
    leave["status"] = "Recalled"
    leave["recalled"] = True
    mock_db.notifications.append({
        "id": f"notif-{len(mock_db.notifications) + 1}",
        "user_id": user_id,
        "title": "Leave Recalled",
        "message": f"Your leave request starting {leave['from_date']} was successfully recalled.",
        "read": False,
        "created_at": now_str
    })
    return {"message": "Leave recalled successfully", "leave": leave}

@router.get("/team-leaves")
def get_team_leaves(month: int, year: int, user_id: str = Depends(get_current_user_id), db = Depends(get_db)):
    if db:
        user_p = db.query(ProfileDB).filter(ProfileDB.id == user_id).first()
        if not user_p or not user_p.manager_id:
            return []
            
        manager_id = user_p.manager_id
        peers = db.query(ProfileDB).filter(ProfileDB.manager_id == manager_id).all()
        peer_ids = [p.id for p in peers]
        
        # Get leaves
        leaves_records = db.query(LeaveDB).filter(LeaveDB.user_id.in_(peer_ids)).all()
        
        team_leaves = []
        for l in leaves_records:
            # Overlap checking
            starts_in_month = (l.from_date.month == month and l.from_date.year == year)
            ends_in_month = (l.to_date.month == month and l.to_date.year == year)
            
            if starts_in_month or ends_in_month:
                peer_p = next(p for p in peers if p.id == l.user_id)
                import json
                try:
                    atts = json.loads(l.attachments) if l.attachments else []
                except Exception:
                    atts = []
                team_leaves.append({
                    "id": l.id,
                    "user_id": l.user_id,
                    "employee_name": peer_p.full_name,
                    "leave_type": l.leave_type,
                    "from_date": l.from_date.isoformat(),
                    "to_date": l.to_date.isoformat(),
                    "num_days": l.num_days,
                    "status": l.status,
                    "attachments": atts
                })
        return team_leaves
        
    # Fallback to mock DB
    user_profile = next((p for p in mock_db.profiles if p["id"] == user_id), None)
    if not user_profile or not user_profile["manager_id"]:
        return []
        
    manager_id = user_profile["manager_id"]
    peers = [p for p in mock_db.profiles if p["manager_id"] == manager_id]
    peer_ids = [p["id"] for p in peers]
    
    team_leaves = []
    for l in mock_db.leaves:
        if l["user_id"] in peer_ids:
            from_d = datetime.date.fromisoformat(l["from_date"])
            to_d = datetime.date.fromisoformat(l["to_date"])
            starts_in_month = (from_d.month == month and from_d.year == year)
            ends_in_month = (to_d.month == month and to_d.year == year)
            
            if starts_in_month or ends_in_month:
                peer_profile = next(p for p in peers if p["id"] == l["user_id"])
                team_leaves.append({
                    "id": l["id"],
                    "user_id": l["user_id"],
                    "employee_name": peer_profile["full_name"],
                    "leave_type": l["leave_type"],
                    "from_date": l["from_date"],
                    "to_date": l["to_date"],
                    "num_days": l["num_days"],
                    "status": l["status"],
                    "attachments": l.get("attachments", [])
                })
    return team_leaves
export_router = router
