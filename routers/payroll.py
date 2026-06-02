from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import datetime
from database import mock_db, get_db, PayrollDB, ClaimDB
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
        payroll_record = db.query(PayrollDB).filter(PayrollDB.user_id == user_id).first()
        if not payroll_record:
            # Dynamically seed live payroll details in Supabase for this employee
            payroll_record = PayrollDB(
                user_id=user_id,
                salary_base=12500.0,
                salary_allowance=4200.0,
                tax_deduction=1850.0,
                increment_history=[
                    {"id": 1, "date": "2024-04-01", "old_salary": 11000.0, "new_salary": 13500.0, "percentage": 22.7},
                    {"id": 2, "date": "2025-04-01", "old_salary": 13500.0, "new_salary": 16700.0, "percentage": 23.7}
                ],
                payslips=[
                    {"month": "May 2026", "net": 14850.0, "download_url": "#"},
                    {"month": "April 2026", "net": 14850.0, "download_url": "#"},
                    {"month": "March 2026", "net": 14850.0, "download_url": "#"}
                ]
            )
            db.add(payroll_record)
            db.commit()
            db.refresh(payroll_record)
            
        return {
            "user_id": payroll_record.user_id,
            "salary_base": payroll_record.salary_base,
            "salary_allowance": payroll_record.salary_allowance,
            "tax_deduction": payroll_record.tax_deduction,
            "increment_history": payroll_record.increment_history,
            "payslips": payroll_record.payslips
        }
        
    # Fallback to mock DB (if Supabase is disconnected)
    # Check if the mock_db has payroll for user_id, if not, copy default
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
