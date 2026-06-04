from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import datetime
from database import mock_db, get_db, TimesheetDB, NotificationDB
from routers.auth import get_current_user_id

router = APIRouter(prefix="/timesheet", tags=["timesheet"])

class TimesheetEntry(BaseModel):
    date: str
    project: str
    hours: float
    description: Optional[str] = ""

class SaveTimesheetRequest(BaseModel):
    week_start: str # YYYY-MM-DD
    entries: List[TimesheetEntry]

class SubmitTimesheetRequest(BaseModel):
    week_start: str # YYYY-MM-DD

def get_start_of_week(date_obj: datetime.date) -> datetime.date:
    return date_obj - datetime.timedelta(days=date_obj.weekday())

@router.get("/current")
def get_current_timesheet(user_id: str = Depends(get_current_user_id), date: str = None, db = Depends(get_db)):
    if date:
        try:
            target_date = datetime.date.fromisoformat(date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format (use YYYY-MM-DD)")
    else:
        target_date = datetime.date.today()
        
    week_start = get_start_of_week(target_date)
    week_start_str = week_start.isoformat()
    week_end = week_start + datetime.timedelta(days=6)
    
    if db:
        timesheet_record = db.query(TimesheetDB).filter(
            TimesheetDB.user_id == user_id,
            TimesheetDB.week_start == week_start
        ).first()
        
        if not timesheet_record:
            # Create a blank timesheet (Mon-Sun)
            entries = []
            for i in range(7):
                day_date = week_start + datetime.timedelta(days=i)
                entries.append({
                    "date": day_date.isoformat(),
                    "project": "None",
                    "hours": 0.0,
                    "description": ""
                })
            timesheet_record = TimesheetDB(
                user_id=user_id,
                week_start=week_start,
                status="Draft",
                entries=entries
            )
            db.add(timesheet_record)
            db.commit()
            db.refresh(timesheet_record)
            
        # Integration 1: Check approved leaves for this week and auto-populate
        from database import LeaveDB
        approved_leaves = db.query(LeaveDB).filter(
            LeaveDB.user_id == user_id,
            LeaveDB.status == 'Approved',
            LeaveDB.from_date <= week_end,
            LeaveDB.to_date >= week_start
        ).all()
        
        leave_map = {}
        for l in approved_leaves:
            curr = max(l.from_date, week_start)
            last = min(l.to_date, week_end)
            while curr <= last:
                leave_map[curr.isoformat()] = {
                    "hours": 4.0 if l.is_half_day else 8.0,
                    "desc": f"Approved Leave ({l.leave_type})"
                }
                curr += datetime.timedelta(days=1)
                
        if timesheet_record.status == 'Draft' and leave_map:
            current_entries = timesheet_record.entries
            modified = False
            updated_entries = []
            for entry in current_entries:
                d_str = entry["date"]
                if d_str in leave_map:
                    if entry["project"] == 'None' or entry["hours"] == 0:
                        entry["project"] = "Leave"
                        entry["hours"] = leave_map[d_str]["hours"]
                        entry["description"] = leave_map[d_str]["desc"]
                        modified = True
                updated_entries.append(entry)
            if modified:
                timesheet_record.entries = updated_entries
                db.commit()
                db.refresh(timesheet_record)
                
        # Integration 2: Query actual attendance hours
        from database import AttendanceLogDB
        attendance_logs = db.query(AttendanceLogDB).filter(
            AttendanceLogDB.user_id == user_id,
            AttendanceLogDB.date >= week_start,
            AttendanceLogDB.date <= week_end
        ).all()
        att_map = {}
        for log in attendance_logs:
            att_map[log.date.isoformat()] = att_map.get(log.date.isoformat(), 0.0) + log.total_hours
            
        attendance_durations = []
        for i in range(7):
            day_date = week_start + datetime.timedelta(days=i)
            d_str = day_date.isoformat()
            attendance_durations.append({
                "date": d_str,
                "hours": round(att_map.get(d_str, 0.0), 2)
            })
            
        return {
            "id": timesheet_record.id,
            "user_id": timesheet_record.user_id,
            "week_start": timesheet_record.week_start.isoformat(),
            "status": timesheet_record.status,
            "entries": timesheet_record.entries,
            "attendance_durations": attendance_durations
        }
        
    return {
        "id": 1,
        "user_id": user_id,
        "week_start": week_start_str,
        "status": "Draft",
        "entries": [],
        "attendance_durations": []
    }

@router.post("/save")
def save_timesheet(data: SaveTimesheetRequest, user_id: str = Depends(get_current_user_id), db = Depends(get_db)):
    # Validation: Daily hours limit should not exceed 24 hours
    from collections import defaultdict
    daily_hours = defaultdict(float)
    for entry in data.entries:
        daily_hours[entry.date] += entry.hours
    for date_str, hrs in daily_hours.items():
        if hrs > 24.0:
            raise HTTPException(status_code=400, detail=f"Total hours logged for {date_str} ({hrs} hrs) exceeds the daily limit of 24 hours.")

    week_start_date = datetime.date.fromisoformat(data.week_start)
    
    if db:
        timesheet_record = db.query(TimesheetDB).filter(
            TimesheetDB.user_id == user_id,
            TimesheetDB.week_start == week_start_date
        ).first()
        
        if not timesheet_record:
            timesheet_record = TimesheetDB(
                user_id=user_id,
                week_start=week_start_date,
                status="Draft"
            )
            db.add(timesheet_record)
            db.flush()
            
        if timesheet_record.status == "Submitted":
            raise HTTPException(status_code=400, detail="Cannot edit a submitted timesheet")
            
        timesheet_record.entries = [entry.dict() for entry in data.entries]
        db.commit()
        return {"message": "Timesheet saved successfully"}
        
    return {"message": "Timesheet saved successfully"}

@router.post("/submit")
def submit_timesheet(data: SubmitTimesheetRequest, user_id: str = Depends(get_current_user_id), db = Depends(get_db)):
    week_start_date = datetime.date.fromisoformat(data.week_start)
    now_str = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
    
    if db:
        timesheet_record = db.query(TimesheetDB).filter(
            TimesheetDB.user_id == user_id,
            TimesheetDB.week_start == week_start_date
        ).first()
        
        if not timesheet_record:
            raise HTTPException(status_code=404, detail="Timesheet not found")
            
        # Validation: Daily hours limit check
        from collections import defaultdict
        daily_hours = defaultdict(float)
        for entry in timesheet_record.raw_entries:
            daily_hours[entry.date.isoformat()] += entry.hours
        for date_str, hrs in daily_hours.items():
            if hrs > 24.0:
                raise HTTPException(status_code=400, detail=f"Total hours logged for {date_str} ({hrs} hrs) exceeds the daily limit of 24 hours.")

        timesheet_record.status = "Submitted"
        
        # Add notification
        new_notif = NotificationDB(
            id=f"notif-{int(datetime.datetime.now().timestamp())}",
            user_id=user_id,
            title="Timesheet Submitted",
            message=f"Your timesheet for week starting {data.week_start} has been submitted for approval.",
            read=False,
            created_at=now_str
        )
        db.add(new_notif)
        db.commit()
        return {"message": "Timesheet submitted successfully"}
        
    return {"message": "Timesheet submitted successfully"}

@router.get("/history")
def get_timesheet_history(user_id: str = Depends(get_current_user_id), db = Depends(get_db)):
    if db:
        records = db.query(TimesheetDB).filter(TimesheetDB.user_id == user_id).order_by(TimesheetDB.week_start.desc()).all()
        return [{
            "id": r.id,
            "week_start": r.week_start.isoformat(),
            "status": r.status,
            "total_hours": sum(e.hours for e in r.raw_entries)
        } for r in records]
    return []

@router.post("/send-reminders")
def send_timesheet_reminders(user_id: str = Depends(get_current_user_id), db = Depends(get_db)):
    if db:
        from database import ProfileDB
        curr_user = db.query(ProfileDB).filter(ProfileDB.id == user_id).first()
        if not curr_user or curr_user.role not in ["HR Manager", "Director"]:
            raise HTTPException(status_code=403, detail="Only HR/Managers can send timesheet reminders.")
            
        employees = db.query(ProfileDB).all()
        today = datetime.date.today()
        week_start = today - datetime.timedelta(days=today.weekday())
        
        sent_count = 0
        from email_notifier import send_email_notification
        
        for emp in employees:
            ts = db.query(TimesheetDB).filter(
                TimesheetDB.user_id == emp.id,
                TimesheetDB.week_start == week_start
            ).first()
            
            if not ts or ts.status != "Submitted":
                subject = "Reminder: Submit Your Weekly Timesheet"
                body_html = f"""
                <p>Dear {emp.full_name},</p>
                <p>This is a reminder to submit your weekly timesheet for the week starting <strong>{week_start.strftime('%d %B %Y')}</strong>.</p>
                <p>Please log in to the portal and submit your timesheet before the end of the day today.</p>
                <p><a href="http://localhost:3000/">Go to YuniQ Portal</a></p>
                """
                body_text = f"Dear {emp.full_name},\n\nThis is a reminder to submit your weekly timesheet for the week starting {week_start.strftime('%d %B %Y')}.\nPlease log in to the portal and submit your timesheet before the end of the day today.\n\nGo to: http://localhost:3000/"
                
                send_email_notification(
                    to_email=emp.email,
                    subject=subject,
                    body_html=body_html,
                    body_text=body_text
                )
                sent_count += 1
                
        return {"message": f"Sent timesheet reminders to {sent_count} employees."}
        
    return {"message": "Mock reminders triggered"}
