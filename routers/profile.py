from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import datetime
import os
import uuid
from database import get_db, ProfileDB, PromotionDB, SalaryRevisionDB, ProfileChangeRequestDB, NotificationDB
from routers.auth import get_current_user_id

router = APIRouter(prefix="/profile", tags=["profile"])

class ProfileChangeRequestSubmit(BaseModel):
    request_data: Dict[str, Any]

class ProfileChangeActionRequest(BaseModel):
    action: str # Approve / Reject
    hr_remarks: Optional[str] = None

def serialize_profile(p: ProfileDB) -> dict:
    return {
        "id": p.id,
        "full_name": p.full_name,
        "email": p.email,
        "role": p.role,
        "department": p.department,
        "manager_id": p.manager_id,
        "avatar_url": p.avatar_url,
        "dob": p.dob.isoformat() if p.dob else None,
        "gender": p.gender,
        "address": p.address,
        "contact_number": p.contact_number,
        "bank_name": p.bank_name,
        "account_number": p.account_number,
        "ifsc_code": p.ifsc_code,
        "pan": p.pan,
        "pf_number": p.pf_number,
        "uan": p.uan,
        "office": p.office,
        "joining_date": p.joining_date.isoformat() if p.joining_date else None,
        "salary": float(p.salary) if p.salary else None,
        "assigned_laptop": p.assigned_laptop
    }

@router.get("/me")
def get_my_profile(user_id: str = Depends(get_current_user_id), db = Depends(get_db)):
    if db:
        p = db.query(ProfileDB).filter(ProfileDB.id == user_id).first()
        if p:
            return serialize_profile(p)
    raise HTTPException(status_code=404, detail="Profile not found")

@router.get("/list")
def get_profiles_list(user_id: str = Depends(get_current_user_id), db = Depends(get_db)):
    """
    Get all profile summaries for corporate directory and dropdown selections.
    """
    if db:
        profiles = db.query(ProfileDB).order_by(ProfileDB.full_name.asc()).all()
        return [{
            "id": p.id,
            "full_name": p.full_name,
            "email": p.email,
            "role": p.role,
            "department": p.department,
            "office": p.office,
            "avatar_url": p.avatar_url
        } for p in profiles]
    return []

@router.get("/teams")
def get_reporting_team(user_id: str = Depends(get_current_user_id), db = Depends(get_db)):
    if db:
        user_p = db.query(ProfileDB).filter(ProfileDB.id == user_id).first()
        if not user_p:
            raise HTTPException(status_code=404, detail="Profile not found")
            
        manager_id = user_p.manager_id
        manager_p = None
        if manager_id:
            manager_record = db.query(ProfileDB).filter(ProfileDB.id == manager_id).first()
            if manager_record:
                manager_p = serialize_profile(manager_record)
                
        # Find peers (profiles sharing the same manager)
        peers_records = []
        if manager_id:
            peers_records = db.query(ProfileDB).filter(ProfileDB.manager_id == manager_id).all()
        else:
            peers_records = db.query(ProfileDB).filter(ProfileDB.manager_id == user_id).all()
            
        return {
            "user": serialize_profile(user_p),
            "manager": manager_p,
            "teammates": [serialize_profile(peer) for peer in peers_records]
        }
    raise HTTPException(status_code=404, detail="Data not found")

@router.post("/photo")
async def upload_profile_photo(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
    db = Depends(get_db)
):
    if not db:
        raise HTTPException(status_code=500, detail="Database connection offline")
        
    p = db.query(ProfileDB).filter(ProfileDB.id == user_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Profile not found")
        
    filename = file.filename or ""
    ext = os.path.splitext(filename)[1].lower()
    allowed_extensions = {".jpg", ".jpeg", ".png"}
    if ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Only JPG, JPEG, and PNG images are supported.")
        
    # Read content & validate size (max 2MB for avatar photo)
    contents = await file.read()
    if len(contents) > 2 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Avatar image size cannot exceed 2MB")
        
    # Save the file
    unique_filename = f"avatar-{user_id}-{uuid.uuid4().hex[:8]}{ext}"
    os.makedirs("uploads", exist_ok=True)
    filepath = os.path.join("uploads", unique_filename)
    
    with open(filepath, "wb") as buffer:
        buffer.write(contents)
        
    # Update profile photo URL path
    p.profile_photo = f"/uploads/{unique_filename}"
    db.commit()
    db.refresh(p)
    return serialize_profile(p)

@router.delete("/photo")
def remove_profile_photo(user_id: str = Depends(get_current_user_id), db = Depends(get_db)):
    if not db:
        raise HTTPException(status_code=500, detail="Database connection offline")
        
    p = db.query(ProfileDB).filter(ProfileDB.id == user_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Profile not found")
        
    p.profile_photo = None
    db.commit()
    db.refresh(p)
    return serialize_profile(p)

@router.get("/career-history/{emp_id}")
def get_career_history(emp_id: str, user_id: str = Depends(get_current_user_id), db = Depends(get_db)):
    if db:
        curr_user = db.query(ProfileDB).filter(ProfileDB.id == user_id).first()
        if not curr_user:
            raise HTTPException(status_code=403, detail="Not authorized")
            
        emp_p = db.query(ProfileDB).filter(ProfileDB.id == emp_id).first()
        if not emp_p:
            raise HTTPException(status_code=404, detail="Employee profile not found")
            
        # Access control: Employee themselves, HR/Director, or direct reporting manager
        is_authorized = (
            user_id == emp_id or
            curr_user.role in ["HR Manager", "Director"] or
            emp_p.manager_id == user_id
        )
        if not is_authorized:
            raise HTTPException(status_code=403, detail="You do not have permission to view this employee's career progression")
            
        promotions = db.query(PromotionDB).filter(PromotionDB.user_id == emp_id).order_by(PromotionDB.date.asc()).all()
        revisions = db.query(SalaryRevisionDB).filter(SalaryRevisionDB.employee_id == emp_id).order_by(SalaryRevisionDB.change_date.asc()).all()
        
        return {
            "joining_date": emp_p.joining_date.isoformat() if emp_p.joining_date else None,
            "initial_role": "Software Engineer",
            "promotions": [{
                "id": p.id,
                "old_role": p.old_role,
                "new_role": p.new_role,
                "date": p.date.isoformat(),
                "details": p.details
            } for p in promotions],
            "salary_revisions": [{
                "id": r.id,
                "change_date": r.change_date.isoformat(),
                "old_salary": float(r.old_salary),
                "new_salary": float(r.new_salary),
                "percentage": r.percentage,
                "remarks": r.remarks
            } for r in revisions]
        }
    return {}

@router.get("/change-requests/my")
def get_my_change_requests(user_id: str = Depends(get_current_user_id), db = Depends(get_db)):
    if db:
        reqs = db.query(ProfileChangeRequestDB).filter(
            ProfileChangeRequestDB.employee_id == user_id
        ).order_by(ProfileChangeRequestDB.created_at.desc()).all()
        
        return [{
            "id": r.id,
            "request_data": r.request_data,
            "status": r.status,
            "created_at": r.created_at.isoformat(),
            "reviewed_at": r.reviewed_at.isoformat() if r.reviewed_at else None,
            "hr_remarks": r.hr_remarks
        } for r in reqs]
    return []

@router.get("/change-requests/all")
def get_all_change_requests(user_id: str = Depends(get_current_user_id), db = Depends(get_db)):
    if db:
        curr_user = db.query(ProfileDB).filter(ProfileDB.id == user_id).first()
        if not curr_user or curr_user.role not in ["HR Manager", "Director"]:
            raise HTTPException(status_code=403, detail="Access denied. HR Managers only.")
            
        reqs = db.query(ProfileChangeRequestDB).order_by(ProfileChangeRequestDB.created_at.desc()).all()
        
        results = []
        for r in reqs:
            emp = db.query(ProfileDB).filter(ProfileDB.id == r.employee_id).first()
            results.append({
                "id": r.id,
                "employee_id": r.employee_id,
                "employee_name": emp.full_name if emp else "Unknown",
                "request_data": r.request_data,
                "status": r.status,
                "created_at": r.created_at.isoformat(),
                "reviewed_at": r.reviewed_at.isoformat() if r.reviewed_at else None,
                "hr_remarks": r.hr_remarks
            })
        return results
    return []

@router.post("/change-request")
def raise_change_request(data: ProfileChangeRequestSubmit, user_id: str = Depends(get_current_user_id), db = Depends(get_db)):
    if db:
        # Verify requested fields are profile properties
        allowed_fields = {
            "address", "contact_number", "personal_email",
            "bank_name", "account_number", "ifsc_code", "pan", "pf_number", "uan"
        }
        filtered_data = {k: v for k, v in data.request_data.items() if k in allowed_fields and v is not None}
        
        if not filtered_data:
            raise HTTPException(status_code=400, detail="No valid profile details to update were provided")
            
        new_req = ProfileChangeRequestDB(
            employee_id=user_id,
            request_data=filtered_data,
            status="Pending",
            created_at=datetime.datetime.now()
        )
        db.add(new_req)
        
        # Add notifications for HR
        hrs = db.query(ProfileDB).filter(ProfileDB.role == "HR Manager").all()
        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
        for hr in hrs:
            db.add(NotificationDB(
                id=f"notif-{int(datetime.datetime.now().timestamp())}-{uuid.uuid4().hex[:4]}",
                user_id=hr.id,
                title="Profile Update Request",
                message=f"Employee {user_id} raised a change request for profile detail updates.",
                read=False,
                created_at=now_str
            ))
            
        db.commit()
        return {"message": "Profile details change request raised successfully"}
    return {"message": "Success"}

@router.post("/change-request/{req_id}/action")
def take_change_request_action(req_id: int, data: ProfileChangeActionRequest, user_id: str = Depends(get_current_user_id), db = Depends(get_db)):
    if db:
        curr_user = db.query(ProfileDB).filter(ProfileDB.id == user_id).first()
        if not curr_user or curr_user.role not in ["HR Manager", "Director"]:
            raise HTTPException(status_code=403, detail="Access denied. HR Managers only.")
            
        req = db.query(ProfileChangeRequestDB).filter(ProfileChangeRequestDB.id == req_id).first()
        if not req:
            raise HTTPException(status_code=404, detail="Change request not found")
        if req.status != "Pending":
            raise HTTPException(status_code=400, detail="Change request has already been processed")
            
        req.status = data.action
        req.hr_remarks = data.hr_remarks
        req.reviewed_at = datetime.datetime.now()
        req.reviewed_by = user_id
        
        # If approved, apply updates to the employee profile master record immediately
        if data.action == "Approve":
            emp = db.query(ProfileDB).filter(ProfileDB.id == req.employee_id).first()
            if emp:
                for k, v in req.request_data.items():
                    if hasattr(emp, k):
                        setattr(emp, k, v)
                        
        # Notify the employee
        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
        db.add(NotificationDB(
            id=f"notif-{int(datetime.datetime.now().timestamp())}",
            user_id=req.employee_id,
            title=f"Change Request: {data.action}d",
            message=f"Your profile update request has been {data.action.lower()}d by HR.{' Remarks: ' + data.hr_remarks if data.hr_remarks else ''}",
            read=False,
            created_at=now_str
        ))
        
        db.commit()
        return {"message": f"Change request successfully {data.action.lower()}d"}
    return {"message": "Processed"}

@router.get("/{profile_id}")
def get_profile_by_id(profile_id: str, db = Depends(get_db)):
    if db:
        p = db.query(ProfileDB).filter(ProfileDB.id == profile_id).first()
        if p:
            return serialize_profile(p)
    raise HTTPException(status_code=404, detail="Profile not found")
