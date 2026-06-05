from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from admin.database import get_db
from admin import models, schemas
import uuid

router = APIRouter(prefix="/auth", tags=["Admin Authentication"])

@router.post("/signup")
def signup(user_in: schemas.UserSignUp, db: Session = Depends(get_db)):
    existing = db.query(models.Employee).filter(models.Employee.email == user_in.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email is already registered."
        )

    name_slug = "".join(c.lower() for c in user_in.full_name if c.isalnum() or c.isspace()).replace(" ", "-")
    short_uuid = uuid.uuid4().hex[:6]
    emp_id = f"user-{name_slug}-{short_uuid}"

    db_user = models.Employee(
        id=emp_id,
        full_name=user_in.full_name,
        email=user_in.email,
        role="HR Manager",
        department="HR",
        manager_id=None,
        salary=100000.0,
        joining_date=None,
        personal_email=user_in.email,
        office="Kolkata",
        status="Active",
        password_hash=user_in.password,
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

    if not user:
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
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email ID or password."
        )

    if user.password_hash and user.password_hash != user_in.password:
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
    import datetime
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
    import datetime
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

    emp.password_hash = data.password
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
