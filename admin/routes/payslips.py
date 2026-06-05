import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from decimal import Decimal
from admin.database import get_db
from admin import models, schemas

router = APIRouter(prefix="/payslips", tags=["Admin Payslips"])

@router.get("/", response_model=List[schemas.PayslipOut])
def get_payslips(db: Session = Depends(get_db)):
    payslips = db.query(models.Payslip).order_by(models.Payslip.year.desc(), models.Payslip.month.desc()).all()
    results = []
    for p in payslips:
        emp = db.query(models.Employee).filter(models.Employee.id == p.employee_id).first()
        results.append(schemas.PayslipOut(
            id=p.id, employee_id=p.employee_id,
            employee_name=emp.full_name if emp else "Unknown",
            month=p.month, year=p.year, basic_salary=p.basic_salary,
            allowances=p.allowances, deductions=p.deductions,
            net_salary=p.net_salary, status=p.status, created_at=p.created_at
        ))
    return results

@router.get("/employee/{employee_id}", response_model=List[schemas.PayslipOut])
def get_employee_payslips(employee_id: str, db: Session = Depends(get_db)):
    payslips = db.query(models.Payslip).filter(models.Payslip.employee_id == employee_id).all()
    results = []
    for p in payslips:
        emp = db.query(models.Employee).filter(models.Employee.id == p.employee_id).first()
        results.append(schemas.PayslipOut(
            id=p.id, employee_id=p.employee_id,
            employee_name=emp.full_name if emp else "Unknown",
            month=p.month, year=p.year, basic_salary=p.basic_salary,
            allowances=p.allowances, deductions=p.deductions,
            net_salary=p.net_salary, status=p.status, created_at=p.created_at
        ))
    return results

@router.post("/", response_model=schemas.PayslipOut)
def generate_payslip(payslip_in: schemas.PayslipCreate, db: Session = Depends(get_db)):
    emp = db.query(models.Employee).filter(models.Employee.id == payslip_in.employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee profile not found.")

    existing = db.query(models.Payslip).filter(
        models.Payslip.employee_id == payslip_in.employee_id,
        models.Payslip.month == payslip_in.month,
        models.Payslip.year == payslip_in.year
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payslip for {payslip_in.month}/{payslip_in.year} already generated."
        )

    annual_salary = emp.salary or Decimal("0")
    basic_salary = Decimal(annual_salary / 12).quantize(Decimal("0.01"))
    net_salary = basic_salary + payslip_in.allowances - payslip_in.deductions

    db_payslip = models.Payslip(
        employee_id=payslip_in.employee_id,
        month=payslip_in.month, year=payslip_in.year,
        basic_salary=basic_salary, allowances=payslip_in.allowances,
        deductions=payslip_in.deductions, net_salary=net_salary,
        status=payslip_in.status
    )
    db.add(db_payslip)

    month_name = datetime.date(1900, payslip_in.month, 1).strftime('%B')
    notif = models.Notification(
        employee_id=payslip_in.employee_id,
        title="Payslip Generated",
        message=f"Your monthly payslip for {month_name} {payslip_in.year} has been generated and paid.",
        read=False
    )
    db.add(notif)
    db.commit()
    db.refresh(db_payslip)

    return schemas.PayslipOut(
        id=db_payslip.id, employee_id=db_payslip.employee_id,
        employee_name=emp.full_name, month=db_payslip.month, year=db_payslip.year,
        basic_salary=db_payslip.basic_salary, allowances=db_payslip.allowances,
        deductions=db_payslip.deductions, net_salary=db_payslip.net_salary,
        status=db_payslip.status, created_at=db_payslip.created_at
    )

@router.delete("/{id}")
def delete_payslip(id: int, db: Session = Depends(get_db)):
    payslip = db.query(models.Payslip).filter(models.Payslip.id == id).first()
    if not payslip:
        raise HTTPException(status_code=404, detail="Payslip record not found.")
    db.delete(payslip)
    db.commit()
    return {"message": "Payslip deleted successfully."}
