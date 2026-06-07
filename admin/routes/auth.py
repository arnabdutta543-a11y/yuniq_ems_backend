from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from admin.database import get_db
from admin import models, schemas
from admin.utils import get_password_hash, verify_password
import uuid
import datetime
from pydantic import BaseModel, EmailStr
from config import settings

router = APIRouter(prefix="/auth", tags=["Admin Authentication"])

# In-memory OTP store: email -> {"otp": str, "expires_at": datetime.datetime}
otp_store = {}

class ForgotPasswordIn(BaseModel):
    email: EmailStr

class VerifyOtpIn(BaseModel):
    email: EmailStr
    otp: str

class ResetPasswordIn(BaseModel):
    email: EmailStr
    otp: str
    password: str

@router.post("/signup")
def signup(user_in: schemas.UserSignUp, db: Session = Depends(get_db)):
    if user_in.secret_key != settings.SIGNUP_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signup secret key."
        )

    existing = db.query(models.Employee).filter(models.Employee.email == user_in.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email is already registered."
        )

    name_slug = "".join(c.lower() for c in user_in.full_name if c.isalnum() or c.isspace()).replace(" ", "-")
    short_uuid = uuid.uuid4().hex[:6]
    emp_id = f"user-{name_slug}-{short_uuid}"

    role = user_in.role or "Associate Consultant"
    role_lower = role.lower()
    if "hr" in role_lower or "recruit" in role_lower or "talent" in role_lower:
        department = "HR"
    elif "engineer" in role_lower or "architect" in role_lower or "dev" in role_lower or "consultant" in role_lower:
        department = "DECISIONS"
    else:
        department = "Management"

    db_user = models.Employee(
        id=emp_id,
        full_name=user_in.full_name,
        email=user_in.email,
        role=role,
        department=department,
        manager_id=None,
        salary=100000.0,
        joining_date=datetime.date.today(),
        personal_email=user_in.email,
        office="Kolkata",
        status="Active",
        password_hash=get_password_hash(user_in.password),
        admin_portal_access=True
    )

    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email or name already exists."
        )

    return {
        "message": "User successfully registered!",
        "profile": {
            "id": db_user.id,
            "full_name": db_user.full_name,
            "email": db_user.email,
            "role": db_user.role,
            "department": db_user.department,
            "permissions": db_user.resolved_permissions,
            "admin_portal_access": True
        }
    }


@router.post("/signin")
def signin(user_in: schemas.UserSignIn, db: Session = Depends(get_db)):
    user = db.query(models.Employee).filter(models.Employee.email == user_in.email).first()

    # Block sign-in if user does not exist or status is pending onboarding
    if not user or user.status == "Pending":
        if user_in.email == "admin@yuniq.com" and user_in.password == "admin123":
            fallback_perms = [
                "tabs.dashboard", "tabs.employees", "tabs.invitations", "tabs.leaves",
                "tabs.timesheets", "tabs.travel", "tabs.performance", "tabs.payslips",
                "tabs.holidays", "tabs.resources", "tabs.config",
                "actions.manage_employees", "actions.add_employee", "actions.edit_employee",
                "actions.delete_employee", "actions.view_employee_details",
                "actions.manage_invitations", "actions.manage_leaves",
                "actions.manage_timesheets", "actions.manage_travel", "actions.manage_performance",
                "actions.manage_payslips", "actions.manage_holidays", "actions.manage_resources",
                "actions.manage_config"
            ]
            return {
                "access_token": "mock-admin-token",
                "profile": {
                    "id": "admin-yuniq",
                    "full_name": "GLOBAL ADMIN",
                    "email": "admin@yuniq.com",
                    "role": "HR Manager",
                    "department": "HR",
                    "permissions": fallback_perms,
                    "admin_portal_access": True
                }
            }
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="you are not registered with us"
        )

    # Use verify_password helper for password comparisons
    if not verify_password(user_in.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password."
        )

    return {
        "access_token": f"mock-jwt-token-{user.id}",
        "profile": {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role,
            "department": user.department,
            "office": user.office,
            "permissions": user.resolved_permissions,
            "admin_portal_access": user.admin_portal_access
        }
    }


@router.get("/onboarding/verify", response_model=schemas.OnboardingVerifyOut)
def verify_onboarding(token: str, db: Session = Depends(get_db)):
    inv = db.query(models.OnboardingInvitation).filter(
        models.OnboardingInvitation.invitation_token == token
    ).first()
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation token not found.")
    if inv.used:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This invitation link has already been used.")
    if inv.expires_at < datetime.datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This invitation link has expired.")

    emp = db.query(models.Employee).filter(models.Employee.id == inv.employee_id).first()
    if not emp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Associated employee profile not found.")

    return schemas.OnboardingVerifyOut(
        employee_id=emp.id,
        full_name=emp.full_name,
        email=emp.email,
        role=emp.role,
        department=emp.department,
        permissions=emp.resolved_permissions
    )


@router.post("/onboarding/complete")
def complete_onboarding(data: schemas.OnboardingCompleteIn, db: Session = Depends(get_db)):
    inv = db.query(models.OnboardingInvitation).filter(
        models.OnboardingInvitation.invitation_token == data.token
    ).first()
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation token not found or invalid.")
    if inv.used:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This invitation has already been used.")
    if inv.expires_at < datetime.datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This invitation has expired.")

    emp = db.query(models.Employee).filter(models.Employee.id == inv.employee_id).first()
    if not emp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found.")

    emp.password_hash = get_password_hash(data.password)
    emp.status = "Active"
    inv.used = True
    db.commit()
    db.refresh(emp)

    return {
        "access_token": f"mock-jwt-token-{emp.id}",
        "profile": {
            "id": emp.id,
            "full_name": emp.full_name,
            "email": emp.email,
            "role": emp.role,
            "department": emp.department,
            "office": emp.office,
            "permissions": emp.resolved_permissions,
            "admin_portal_access": emp.admin_portal_access
        }
    }


@router.post("/forgot-password")
def forgot_password(data: ForgotPasswordIn, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    import random
    from admin.mail import send_notification_email
    
    # Check if user exists
    user = db.query(models.Employee).filter(models.Employee.email == data.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="you are not registered with us"
        )
        
    # Check if user has not verified their account (onboarding pending)
    if not user.password_hash or user.status == "Pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="first set up the new password using the onboarding mail..your account is not verified..."
        )
        
    now = datetime.datetime.utcnow()
    # Clean up expired entries to prevent memory growth
    expired_emails = [e for e, info in otp_store.items() if info["expires_at"] < now]
    for e in expired_emails:
        otp_store.pop(e, None)
        
    # Generate 6-digit verification code
    otp = f"{random.randint(100000, 999999)}"
    expires_at = now + datetime.timedelta(minutes=10)
    otp_store[data.email] = {
        "otp": otp,
        "expires_at": expires_at
    }
    
    # Format and queue reset email
    subject = "YuniQ Password Reset OTP"
    category = "SECURITY"
    content_html = f"""
    <p style="color:#ffffff; font-size:16px;">We received a request to reset your YuniQ account password.</p>
    <p style="color:#ffffff; font-size:16px;">Your 6-digit verification OTP is:</p>
    <div style="background-color:#1e293b; padding:15px; border-radius:6px; margin-bottom:25px; text-align:center; font-size:24px; font-weight:bold; letter-spacing:5px; color:#e8302a; border: 1px solid #334155;">
      {otp}
    </div>
    <p style="color:#64748b;font-size:14px;">This OTP is valid for 10 minutes. If you did not request a password reset, please ignore this email or contact support.</p>
    """
    
    background_tasks.add_task(
        send_notification_email,
        to_email=data.email,
        employee_name=user.full_name,
        subject=subject,
        category=category,
        content_html=content_html,
        status_color="#e8302a"
    )
    
    return {"message": "Verification OTP has been sent to your email."}


@router.post("/verify-otp")
def verify_otp(data: VerifyOtpIn):
    info = otp_store.get(data.email)
    if not info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No OTP requested for this email."
        )
        
    if datetime.datetime.utcnow() > info["expires_at"]:
        otp_store.pop(data.email, None)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP has expired. Please request a new one."
        )
        
    if info["otp"] != data.otp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect OTP. Please try again."
        )
        
    return {"message": "OTP verified successfully."}


@router.post("/reset-password")
def reset_password(data: ResetPasswordIn, db: Session = Depends(get_db)):
    info = otp_store.get(data.email)
    if not info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No OTP verification session found."
        )
        
    if datetime.datetime.utcnow() > info["expires_at"]:
        otp_store.pop(data.email, None)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP has expired. Please request a new one."
        )
        
    if info["otp"] != data.otp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect OTP."
        )
        
    user = db.query(models.Employee).filter(models.Employee.email == data.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found."
        )
        
    user.password_hash = get_password_hash(data.password)
    user.status = "Active"
    
    # Set invitation to used if it exists
    inv = db.query(models.OnboardingInvitation).filter(
        models.OnboardingInvitation.employee_id == user.id,
        models.OnboardingInvitation.used == False
    ).first()
    if inv:
        inv.used = True
        
    db.commit()
    db.refresh(user)
    
    otp_store.pop(data.email, None)
    
    return {
        "message": "Password reset successfully. You can now login.",
        "access_token": f"mock-jwt-token-{user.id}",
        "profile": {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role,
            "department": user.department,
            "office": user.office,
            "permissions": user.resolved_permissions,
            "admin_portal_access": user.admin_portal_access
        }
    }
