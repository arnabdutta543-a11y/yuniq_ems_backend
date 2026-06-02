from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import datetime
from database import mock_db
from routers.auth import get_current_user_id
from email_notifier import send_email_notification

router = APIRouter(prefix="/leave", tags=["leave"])

class ApplyLeaveRequest(BaseModel):
    leave_type: str
    from_date: str # YYYY-MM-DD
    to_date: str # YYYY-MM-DD
    num_days: float
    reason: str

@router.get("/my-leaves")
def get_my_leaves(user_id: str = Depends(get_current_user_id)):
    """
    Get all leave requests of the user.
    """
    user_leaves = [l for l in mock_db.leaves if l["user_id"] == user_id]
    # Sort by from_date descending
    user_leaves.sort(key=lambda x: x["from_date"], reverse=True)
    return user_leaves

@router.get("/balance")
def get_leave_balance(user_id: str = Depends(get_current_user_id)):
    """
    Calculate leave balance, leave taken, and LOP for the current year.
    We return values that closely match the screens:
    Leave Balance: 10.5, Leave Taken: 18.5, LOP: 0
    """
    # Sum up approved leaves
    user_leaves = [l for l in mock_db.leaves if l["user_id"] == user_id]
    
    # In mock db we pre-populate and keep it consistent
    # Let's count them
    approved_taken = sum(l["num_days"] for l in user_leaves if l["status"] == "Approved")
    recalled_taken = sum(l["num_days"] for l in user_leaves if l["status"] == "Recalled")
    
    # For representation consistency with user screenshots:
    # leave taken = 18.5
    # leave balance = 10.5
    # LOP = 0
    # Let's calculate dynamically if there are new applications
    base_balance = 29.0
    taken = approved_taken
    balance = base_balance - taken
    lop = 0.0
    
    return {
        "balance": max(0.0, balance),
        "taken": taken,
        "lop": lop
    }

@router.post("/apply")
def apply_leave(data: ApplyLeaveRequest, user_id: str = Depends(get_current_user_id)):
    # Validate dates
    try:
        from_d = datetime.date.fromisoformat(data.from_date)
        to_d = datetime.date.fromisoformat(data.to_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format (use YYYY-MM-DD)")
        
    if from_d > to_d:
        raise HTTPException(status_code=400, detail="From date cannot be after To date")
        
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
    
    # Notify Manager via mock email and notification
    profile = next(p for p in mock_db.profiles if p["id"] == user_id)
    manager = next((p for p in mock_db.profiles if p["id"] == profile["manager_id"]), None)
    
    if manager:
        send_email_notification(
            to_email=manager["email"],
            subject=f"Leave Application: {profile['full_name']}",
            body_html=f"<p>{profile['full_name']} has applied for leave from {data.from_date} to {data.to_date}. Reason: {data.reason}</p>",
            body_text=f"{profile['full_name']} applied for leave from {data.from_date} to {data.to_date}.\nReason: {data.reason}"
        )
        
    # User notification
    now_str = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
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
def recall_leave(leave_id: int, user_id: str = Depends(get_current_user_id)):
    leave = next((l for l in mock_db.leaves if l["id"] == leave_id and l["user_id"] == user_id), None)
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")
        
    leave["status"] = "Recalled"
    leave["recalled"] = True
    
    # User notification
    now_str = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
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
def get_team_leaves(month: int, year: int, user_id: str = Depends(get_current_user_id)):
    """
    Get all approved/pending leaves of team members (peers sharing same manager)
    for a specific month & year.
    Used for Team Leave Calendar view.
    """
    user_profile = next((p for p in mock_db.profiles if p["id"] == user_id), None)
    if not user_profile:
        raise HTTPException(status_code=404, detail="Profile not found")
        
    manager_id = user_profile["manager_id"]
    if not manager_id:
        return []
        
    # Get peers
    peers = [p for p in mock_db.profiles if p["manager_id"] == manager_id]
    peer_ids = [p["id"] for p in peers]
    
    team_leaves = []
    for l in mock_db.leaves:
        if l["user_id"] in peer_ids:
            # Parse dates and filter by month/year overlap
            from_d = datetime.date.fromisoformat(l["from_date"])
            to_d = datetime.date.fromisoformat(l["to_date"])
            
            # Check if this leave overlaps with target month
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
