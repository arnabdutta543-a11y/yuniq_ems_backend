import uuid
import datetime
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Header
from sqlalchemy.orm import Session
from typing import List, Optional
from admin.database import get_db
from admin import models, schemas
from admin.mail import send_onboarding_email

router = APIRouter(prefix="/employees", tags=["Admin Employees"])

def slugify(text: str) -> str:
    return "".join(c.lower() for c in text if c.isalnum() or c.isspace()).replace(" ", "-")

@router.get("/", response_model=List[schemas.EmployeeOut])
def get_employees(
    department: Optional[str] = None,
    role: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Employee)
    if department:
        query = query.filter(models.Employee.department.ilike(department))
    if role:
        query = query.filter(models.Employee.role.ilike(role))
    if status:
        query = query.filter(models.Employee.status == status)
    return query.all()

@router.get("/managers", response_model=List[schemas.EmployeeOut])
def get_managers(db: Session = Depends(get_db)):
    return db.query(models.Employee).filter(
        models.Employee.role.in_([
            "Director", "Manager", "CEO", "Senior Manager", "HR Manager", "Management"
        ])
    ).all()

@router.get("/invitations", response_model=List[schemas.OnboardingInvitationOut])
def get_invitations(db: Session = Depends(get_db)):
    invitations = db.query(models.OnboardingInvitation).all()
    results = []
    for inv in invitations:
        emp = db.query(models.Employee).filter(models.Employee.id == inv.employee_id).first()
        results.append(schemas.OnboardingInvitationOut(
            id=inv.id,
            employee_id=inv.employee_id,
            employee_name=emp.full_name if emp else "Unknown",
            email=inv.email,
            invitation_token=inv.invitation_token,
            expires_at=inv.expires_at,
            used=inv.used,
            created_at=inv.created_at
        ))
    return results

@router.get("/{id}", response_model=schemas.EmployeeOut)
def get_employee(id: str, db: Session = Depends(get_db)):
    employee = db.query(models.Employee).filter(models.Employee.id == id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee

@router.post("/", response_model=schemas.EmployeeOut)
def create_employee(
    emp_in: schemas.EmployeeCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    x_sender_name: Optional[str] = Header(None)
):
    existing = db.query(models.Employee).filter(models.Employee.email == emp_in.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employee with this email already exists"
        )

    if emp_in.custom_id and emp_in.custom_id.strip():
        suffix = emp_in.custom_id.replace("TEK-", "").strip()
        emp_id = f"TEK-{suffix}"
    else:
        existing_ids = db.query(models.Employee.id).filter(models.Employee.id.like("TEK-%")).all()
        max_num = 0
        for (eid,) in existing_ids:
            try:
                parts = eid.split("-")
                if len(parts) >= 2 and parts[1].isdigit():
                    num = int(parts[1])
                    if num > max_num:
                        max_num = num
            except ValueError:
                pass
        emp_id = f"TEK-{max_num + 1}"

    check_id = db.query(models.Employee).filter(models.Employee.id == emp_id).first()
    if check_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Employee ID {emp_id} already exists"
        )

    manager_id = emp_in.manager_id
    if emp_in.role in ["Director", "Manager", "CEO", "Senior Manager", "HR Manager"]:
        manager_id = None

    import json
    permissions_json = json.dumps(emp_in.permissions) if emp_in.permissions is not None else None
    if not emp_in.admin_portal_access:
        permissions_json = None

    db_employee = models.Employee(
        id=emp_id,
        full_name=emp_in.full_name,
        email=emp_in.email,
        role=emp_in.role,
        department=emp_in.department,
        manager_id=manager_id,
        salary=emp_in.salary,
        joining_date=emp_in.joining_date,
        personal_email=emp_in.email,
        office=emp_in.office,
        assigned_laptop=emp_in.assigned_laptop,
        status="Pending",
        permissions=permissions_json,
        dob=emp_in.dob,
        gender=emp_in.gender,
        address=emp_in.address,
        contact_number=emp_in.contact_number,
        bank_name=emp_in.bank_name,
        account_number=emp_in.account_number,
        ifsc_code=emp_in.ifsc_code,
        pan=emp_in.pan,
        pf_number=emp_in.pf_number,
        uan=emp_in.uan,
        admin_portal_access=emp_in.admin_portal_access
    )

    db.add(db_employee)

    if emp_in.assigned_laptop and emp_in.assigned_laptop.strip():
        laptop_asset_id = emp_in.assigned_laptop.strip()
        existing_res = db.query(models.Resource).filter(models.Resource.asset_id == laptop_asset_id).first()
        if existing_res:
            existing_res.employee_id = emp_id
            existing_res.status = "Allocated"
        else:
            db_resource = models.Resource(
                name="Laptop",
                asset_id=laptop_asset_id,
                employee_id=emp_id,
                status="Allocated"
            )
            db.add(db_resource)

    db.flush()

    invitation_token = str(uuid.uuid4())
    expires_at = datetime.datetime.utcnow() + datetime.timedelta(days=7)

    db_invitation = models.OnboardingInvitation(
        employee_id=emp_id,
        email=emp_in.email,
        invitation_token=invitation_token,
        expires_at=expires_at,
        used=False
    )
    db.add(db_invitation)
    db.commit()
    db.refresh(db_employee)

    background_tasks.add_task(
        send_onboarding_email,
        to_email=emp_in.email,
        employee_name=emp_in.full_name,
        invitation_token=invitation_token,
        role=emp_in.role,
        sender_name=x_sender_name
    )

    return db_employee

@router.put("/{id}", response_model=schemas.EmployeeOut)
def update_employee(id: str, emp_in: schemas.EmployeeUpdate, db: Session = Depends(get_db)):
    employee = db.query(models.Employee).filter(models.Employee.id == id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    update_data = emp_in.model_dump(exclude_unset=True)

    if "permissions" in update_data:
        import json
        if update_data["permissions"] is not None:
            update_data["permissions"] = json.dumps(update_data["permissions"])
        else:
            update_data["permissions"] = None

    portal_access = update_data.get("admin_portal_access", employee.admin_portal_access)
    if not portal_access:
        update_data["permissions"] = None

    if "role" in update_data and update_data["role"] in ["Director", "Manager", "CEO", "Senior Manager", "HR Manager"]:
        update_data["manager_id"] = None

    if "assigned_laptop" in update_data:
        new_laptop = update_data["assigned_laptop"]
        old_laptop = employee.assigned_laptop
        if new_laptop != old_laptop:
            if old_laptop:
                prev_res = db.query(models.Resource).filter(
                    models.Resource.asset_id == old_laptop,
                    models.Resource.employee_id == employee.id
                ).first()
                if prev_res:
                    prev_res.employee_id = None
                    prev_res.status = "Available"

            if new_laptop and new_laptop.strip():
                laptop_asset_id = new_laptop.strip()
                existing_res = db.query(models.Resource).filter(models.Resource.asset_id == laptop_asset_id).first()
                if existing_res:
                    existing_res.employee_id = employee.id
                    existing_res.status = "Allocated"
                else:
                    db_resource = models.Resource(
                        name="Laptop",
                        asset_id=laptop_asset_id,
                        employee_id=employee.id,
                        status="Allocated"
                    )
                    db.add(db_resource)

    for field, value in update_data.items():
        setattr(employee, field, value)

    db.commit()
    db.refresh(employee)
    return employee

@router.delete("/{id}", response_model=schemas.EmployeeOut)
def delete_employee(id: str, db: Session = Depends(get_db)):
    employee = db.query(models.Employee).filter(models.Employee.id == id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    db.delete(employee)
    db.commit()
    return employee

@router.post("/invitations/{inv_id}/resend")
def resend_invitation(
    inv_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    inv = db.query(models.OnboardingInvitation).filter(models.OnboardingInvitation.id == inv_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invitation not found")

    emp = db.query(models.Employee).filter(models.Employee.id == inv.employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found for this invitation")

    new_token = str(uuid.uuid4())
    inv.invitation_token = new_token
    inv.expires_at = datetime.datetime.utcnow() + datetime.timedelta(days=7)
    inv.used = False
    db.commit()

    background_tasks.add_task(
        send_onboarding_email,
        to_email=inv.email,
        employee_name=emp.full_name,
        invitation_token=new_token,
        role=emp.role
    )

    return {"message": "Onboarding invitation resent successfully", "new_token": new_token}


# ─── Bank Details ─────────────────────────────────────────────────────────────

@router.post("/{id}/bank-details", response_model=schemas.BankDetailsOut)
def save_bank_details(id: str, bd_in: schemas.BankDetailsBase, db: Session = Depends(get_db)):
    emp = db.query(models.Employee).filter(models.Employee.id == id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    emp.bank_name = bd_in.bank_name
    emp.account_number = bd_in.account_number
    emp.ifsc_code = bd_in.ifsc_code
    db.commit()
    return schemas.BankDetailsOut(
        id=1, employee_id=emp.id, bank_name=emp.bank_name or "",
        account_number=emp.account_number or "", ifsc_code=emp.ifsc_code or "",
        account_type=bd_in.account_type or "Savings", created_at=emp.created_at
    )

@router.get("/{id}/bank-details", response_model=schemas.BankDetailsOut)
def get_bank_details(id: str, db: Session = Depends(get_db)):
    emp = db.query(models.Employee).filter(models.Employee.id == id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    if not emp.bank_name:
        raise HTTPException(status_code=404, detail="Bank details not found")
    return schemas.BankDetailsOut(
        id=1, employee_id=emp.id, bank_name=emp.bank_name,
        account_number=emp.account_number or "", ifsc_code=emp.ifsc_code or "",
        account_type="Savings", created_at=emp.created_at
    )


# ─── PAN Info ─────────────────────────────────────────────────────────────────

@router.post("/{id}/pan-info", response_model=schemas.PANInfoOut)
def save_pan_info(id: str, pan_in: schemas.PANInfoBase, db: Session = Depends(get_db)):
    emp = db.query(models.Employee).filter(models.Employee.id == id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    emp.pan = pan_in.pan_number
    emp.pf_number = pan_in.pf_number
    emp.uan = pan_in.uan_number
    db.commit()
    return schemas.PANInfoOut(
        id=1, employee_id=emp.id, pan_number=emp.pan or "",
        pf_number=emp.pf_number or "", uan_number=emp.uan or "", created_at=emp.created_at
    )

@router.get("/{id}/pan-info", response_model=schemas.PANInfoOut)
def get_pan_info(id: str, db: Session = Depends(get_db)):
    emp = db.query(models.Employee).filter(models.Employee.id == id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    if not emp.pan and not emp.pf_number and not emp.uan:
        raise HTTPException(status_code=404, detail="PAN info not found")
    return schemas.PANInfoOut(
        id=1, employee_id=emp.id, pan_number=emp.pan or "",
        pf_number=emp.pf_number or "", uan_number=emp.uan or "", created_at=emp.created_at
    )


# ─── Leave Summary ────────────────────────────────────────────────────────────

@router.get("/{id}/leave-summary", response_model=schemas.LeaveSummaryOut)
def get_employee_leave_summary(id: str, db: Session = Depends(get_db)):
    emp = db.query(models.Employee).filter(models.Employee.id == id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    current_year = datetime.date.today().year
    emp_leave_year = emp.leave_year if emp.leave_year is not None else current_year
    carry_forward = 0

    if emp_leave_year < current_year:
        carry_forward = min(emp.leave_balance if emp.leave_balance is not None else 0, 5)
        emp.paid_leaves = 24 + carry_forward
        emp.leave_balance = 24 + carry_forward
        emp.lop_days = 0
        emp.leave_year = current_year
        db.commit()
        db.refresh(emp)
    else:
        carry_forward = (emp.paid_leaves or 24) - 24

    year_start = datetime.date(current_year, 1, 1)
    year_end = datetime.date(current_year, 12, 31)

    year_leaves = (
        db.query(models.Leave)
        .filter(
            models.Leave.employee_id == id,
            models.Leave.from_date >= year_start,
            models.Leave.from_date <= year_end,
        )
        .order_by(models.Leave.from_date.desc())
        .all()
    )

    approved_taken = sum(float(l.num_days) for l in year_leaves if l.status == "Approved")
    base_leaves = emp.paid_leaves if emp.paid_leaves is not None else 24
    expected_balance = max(0, int(base_leaves - approved_taken))
    expected_lop = max(0, int(approved_taken - base_leaves))

    if emp.leave_balance != expected_balance or emp.lop_days != expected_lop:
        emp.leave_balance = expected_balance
        emp.lop_days = expected_lop
        db.commit()
        db.refresh(emp)

    leave_history = [
        schemas.LeaveOut(
            id=l.id, employee_id=l.employee_id, employee_name=emp.full_name,
            leave_type=l.leave_type, from_date=l.from_date, to_date=l.to_date,
            num_days=l.num_days, reason=l.reason, status=l.status,
            applied_date=l.applied_date, recalled=l.recalled,
        )
        for l in year_leaves
    ]

    return schemas.LeaveSummaryOut(
        employee_id=emp.id,
        employee_name=emp.full_name,
        paid_leaves=emp.paid_leaves if emp.paid_leaves is not None else 24,
        leaves_taken=int(approved_taken),
        leave_balance=emp.leave_balance if emp.leave_balance is not None else 24,
        lop_days=emp.lop_days if emp.lop_days is not None else 0,
        leave_year=emp.leave_year if emp.leave_year is not None else current_year,
        carry_forward=carry_forward,
        leave_history=leave_history,
    )
