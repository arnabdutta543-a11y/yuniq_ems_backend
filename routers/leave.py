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

def serialize_leave(l: LeaveDB) -> dict:
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
        "recalled": l.recalled
    }

@router.get("/my-leaves")
def get_my_leaves(user_id: str = Depends(get_current_user_id), db = Depends(get_db)):
    if db:
        leaves_records = db.query(LeaveDB).filter(LeaveDB.user_id == user_id).order_by(LeaveDB.from_date.desc()).all()
        return [serialize_leave(l) for l in leaves_records]
        
    # Fallback to mock DB
    user_leaves = [l for l in mock_db.leaves if l["user_id"] == user_id]
    user_leaves.sort(key=lambda x: x["from_date"], reverse=True)
    return user_leaves

@router.get("/balance")
def get_leave_balance(user_id: str = Depends(get_current_user_id), db = Depends(get_db)):
    if db:
        leaves_records = db.query(LeaveDB).filter(LeaveDB.user_id == user_id).all()
        approved_taken = sum(l.num_days for l in leaves_records if l.status == "Approved")
        recalled_taken = sum(l.num_days for l in leaves_records if l.status == "Recalled")
        
        base_balance = 29.0
        taken = approved_taken
        balance = base_balance - taken
        return {
            "balance": max(0.0, balance),
            "taken": taken,
            "lop": 0.0
        }
        
    # Fallback to mock DB
    user_leaves = [l for l in mock_db.leaves if l["user_id"] == user_id]
    approved_taken = sum(l["num_days"] for l in user_leaves if l["status"] == "Approved")
    base_balance = 29.0
    taken = approved_taken
    balance = base_balance - taken
    return {
        "balance": max(0.0, balance),
        "taken": taken,
        "lop": 0.0
    }

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
        new_leave = LeaveDB(
            user_id=user_id,
            leave_type=data.leave_type,
            from_date=from_d,
            to_date=to_d,
            num_days=data.num_days,
            reason=data.reason,
            status="Pending",
            applied_date=datetime.date.today(),
            recalled=False
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
        
    # Fallback to mock DB
    new_leave = {
        "id": len(mock_db.leaves) + 1,
        "user_id": user_id,
        "leave_type": data.leave_type,
        "from_date": data.from_date,
        "to_date": data.to_date,
        "num_days": data.num_days,
        "reason": data.reason,
        "status": "Pending",
        "applied_date": datetime.date.today().isoformat(),
        "recalled": False
    }
    mock_db.leaves.append(new_leave)
    profile = next(p for p in mock_db.profiles if p["id"] == user_id)
    manager = next((p for p in mock_db.profiles if p["id"] == profile["manager_id"]), None)
    if manager:
        send_email_notification(
            to_email=manager["email"],
            subject=f"Leave Application: {profile['full_name']}",
            body_html=f"<p>{profile['full_name']} has applied for leave from {data.from_date} to {data.to_date}. Reason: {data.reason}</p>",
            body_text=f"{profile['full_name']} applied for leave from {data.from_date} to {data.to_date}.\nReason: {data.reason}"
        )
    mock_db.notifications.append({
        "id": f"notif-{len(mock_db.notifications) + 1}",
        "user_id": user_id,
        "title": "Leave Applied",
        "message": f"Your leave request for {data.from_date} has been submitted for approval.",
        "read": False,
        "created_at": now_str
    })
    return {"message": "Leave applied successfully", "leave": new_leave}

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
                team_leaves.append({
                    "id": l.id,
                    "user_id": l.user_id,
                    "employee_name": peer_p.full_name,
                    "leave_type": l.leave_type,
                    "from_date": l.from_date.isoformat(),
                    "to_date": l.to_date.isoformat(),
                    "num_days": l.num_days,
                    "status": l.status
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
                    "status": l["status"]
                })
    return team_leaves
export_router = router
