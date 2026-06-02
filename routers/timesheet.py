from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any
import datetime
from database import mock_db
from routers.auth import get_current_user_id

router = APIRouter(prefix="/timesheet", tags=["timesheet"])

class TimesheetEntry(BaseModel):
    date: str
    project: str
    hours: float
    description: str

class SaveTimesheetRequest(BaseModel):
    week_start: str # YYYY-MM-DD
    entries: List[TimesheetEntry]

class SubmitTimesheetRequest(BaseModel):
    week_start: str # YYYY-MM-DD

def get_start_of_week(date_obj: datetime.date) -> datetime.date:
    # Next.js UI shows Monday as start of week
    return date_obj - datetime.timedelta(days=date_obj.weekday())

@router.get("/current")
def get_current_timesheet(user_id: str = Depends(get_current_user_id), date: str = None):
    """
    Get timesheet for the week containing the specified date (default today).
    If none exists, create a new draft timesheet.
    """
    if date:
        try:
            target_date = datetime.date.fromisoformat(date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format (use YYYY-MM-DD)")
    else:
        target_date = datetime.date.today()
        
    week_start = get_start_of_week(target_date)
    week_start_str = week_start.isoformat()
    
    # Try to find existing timesheet
    timesheet = next((ts for ts in mock_db.timesheets 
                      if ts["user_id"] == user_id and ts["week_start"] == week_start_str), None)
                      
    if not timesheet:
        # Create a blank timesheet for this week (Mon-Sun)
        entries = []
        for i in range(7):
            day_date = week_start + datetime.timedelta(days=i)
            entries.append({
                "date": day_date.isoformat(),
                "project": "None",
                "hours": 0.0,
                "description": ""
            })
            
        timesheet = {
            "id": f"ts-{len(mock_db.timesheets) + 1}",
            "user_id": user_id,
            "week_start": week_start_str,
            "status": "Draft",
            "entries": entries
        }
        mock_db.timesheets.append(timesheet)
        
    return timesheet

@router.post("/save")
def save_timesheet(data: SaveTimesheetRequest, user_id: str = Depends(get_current_user_id)):
    timesheet = next((ts for ts in mock_db.timesheets 
                      if ts["user_id"] == user_id and ts["week_start"] == data.week_start), None)
                      
    if not timesheet:
        raise HTTPException(status_code=404, detail="Timesheet not found")
        
    if timesheet["status"] == "Submitted":
        raise HTTPException(status_code=400, detail="Cannot edit a submitted timesheet")
        
    # Update entries
    timesheet["entries"] = [entry.dict() for entry in data.entries]
    return {"message": "Timesheet saved successfully", "timesheet": timesheet}

@router.post("/submit")
def submit_timesheet(data: SubmitTimesheetRequest, user_id: str = Depends(get_current_user_id)):
    timesheet = next((ts for ts in mock_db.timesheets 
                      if ts["user_id"] == user_id and ts["week_start"] == data.week_start), None)
                      
    if not timesheet:
        raise HTTPException(status_code=404, detail="Timesheet not found")
        
    timesheet["status"] = "Submitted"
    
    # Notify user
    now_str = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
    mock_db.notifications.append({
        "id": f"notif-{len(mock_db.notifications) + 1}",
        "user_id": user_id,
        "title": "Timesheet Submitted",
        "message": f"Your timesheet for week starting {data.week_start} has been submitted for approval.",
        "read": False,
        "created_at": now_str
    })
    
    return {"message": "Timesheet submitted successfully", "timesheet": timesheet}
