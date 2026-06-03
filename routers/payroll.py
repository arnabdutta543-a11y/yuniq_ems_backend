from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import datetime
from database import mock_db, get_db, PayrollDB, ClaimDB, ProfileDB
from routers.auth import get_current_user_id

router = APIRouter(prefix="/payroll", tags=["payroll"])

class ClaimRequest(BaseModel):
    amount: float
    category: str
    description: str
    date: str # YYYY-MM-DD

@router.get("/details")
def get_payroll_details(user_id: str = Depends(get_current_user_id), db = Depends(get_db)):
    if db:
        # Get employee info
        emp = db.query(ProfileDB).filter(ProfileDB.id == user_id).first()
        if not emp:
            raise HTTPException(status_code=404, detail="Employee not found")
            
        # Get payslips from payslips table (mapped via PayrollDB)
        payslips_records = db.query(PayrollDB).filter(PayrollDB.user_id == user_id).order_by(PayrollDB.year.desc(), PayrollDB.month.desc()).all()
        
        # If no payslips exist, create one for May 2026 based on employee's salary
        if not payslips_records:
            salary_val = float(emp.salary) if emp.salary else 1800000.0
            # If annual, monthly is salary/12. If already monthly, keep as is.
            monthly_base = salary_val / 12.0 if salary_val >= 100000 else salary_val
            allowance = monthly_base * 0.10
            deductions = monthly_base * 0.05
            net = monthly_base + allowance - deductions
            
            new_slip = PayrollDB(
                user_id=user_id,
                month=5,
                year=2026,
                salary_base=monthly_base,
                salary_allowance=allowance,
                tax_deduction=deductions,
                net=net,
                status="Paid"
            )
            db.add(new_slip)
            db.commit()
            db.refresh(new_slip)
            payslips_records = [new_slip]
            
        latest = payslips_records[0]
        month_names = ["", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        
        payslips_list = []
        for p in payslips_records:
            month_str = month_names[p.month] if 1 <= p.month <= 12 else str(p.month)
            payslips_list.append({
                "month": f"{month_str} {p.year}",
                "net": float(p.net),
                "basic_salary": float(p.salary_base),
                "allowances": float(p.salary_allowance),
                "deductions": float(p.tax_deduction),
                "status": p.status
            })
            
        increment_history = [
            {"id": 1, "date": "2024-04-01", "old_salary": float(latest.salary_base) * 0.8, "new_salary": float(latest.salary_base) * 0.9, "percentage": 12.5},
            {"id": 2, "date": "2025-04-01", "old_salary": float(latest.salary_base) * 0.9, "new_salary": float(latest.salary_base), "percentage": 11.1}
        ]
        
        return {
            "user_id": user_id,
            "salary_base": float(latest.salary_base),
            "salary_allowance": float(latest.salary_allowance),
            "tax_deduction": float(latest.tax_deduction),
            "increment_history": increment_history,
            "payslips": payslips_list
        }
        
    # Fallback to mock DB (if Supabase is disconnected)
    if mock_db.payroll.get("user_id") != user_id:
        mock_db.payroll["user_id"] = user_id
    return mock_db.payroll

@router.get("/claims")
def get_claims(user_id: str = Depends(get_current_user_id), db = Depends(get_db)):
    if db:
        claims = db.query(ClaimDB).filter(ClaimDB.user_id == user_id).order_by(ClaimDB.date.desc()).all()
        return [{
            "id": c.id,
            "user_id": c.user_id,
            "amount": c.amount,
            "category": c.category,
            "description": c.description,
            "date": c.date.isoformat(),
            "status": c.status
        } for c in claims]
        
    return [c for c in mock_db.claims if c["user_id"] == user_id]

@router.post("/claim")
def submit_claim(data: ClaimRequest, user_id: str = Depends(get_current_user_id), db = Depends(get_db)):
    try:
        claim_date = datetime.date.fromisoformat(data.date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format (use YYYY-MM-DD)")
        
    if db:
        new_claim = ClaimDB(
            user_id=user_id,
            amount=data.amount,
            category=data.category,
            description=data.description,
            date=claim_date,
            status="Pending"
        )
        db.add(new_claim)
        db.commit()
        return {"message": "Claim submitted successfully", "claim_id": new_claim.id}
        
    # Mock fallback
    new_id = max([c["id"] for c in mock_db.claims]) + 1 if mock_db.claims else 1
    new_claim_mock = {
        "id": new_id,
        "user_id": user_id,
        "amount": data.amount,
        "category": data.category,
        "description": data.description,
        "date": data.date,
        "status": "Pending"
    }
    mock_db.claims.append(new_claim_mock)
    return {"message": "Claim submitted successfully", "claim": new_claim_mock}
