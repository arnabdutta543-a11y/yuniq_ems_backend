from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from admin.database import get_db
from admin import models, schemas

router = APIRouter(prefix="/appraisals", tags=["Admin Appraisals"])

@router.get("/", response_model=List[schemas.OKROut])
def get_appraisals(
    employee_id: Optional[str] = None,
    manager_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.OKR)
    if employee_id:
        query = query.filter(models.OKR.employee_id == employee_id)
    elif manager_id:
        subordinates = db.query(models.Employee.id).filter(models.Employee.manager_id == manager_id).all()
        sub_ids = [sub[0] for sub in subordinates]
        query = query.filter(models.OKR.employee_id.in_(sub_ids))

    okrs = query.all()
    results = []
    for okr in okrs:
        emp = db.query(models.Employee).filter(models.Employee.id == okr.employee_id).first()
        results.append(schemas.OKROut(
            id=okr.id, employee_id=okr.employee_id, type=okr.type,
            objective=okr.objective, key_results=okr.key_results,
            progress=float(okr.progress) if okr.progress is not None else 0.0,
            year=okr.year, quarter=okr.quarter, due_date=okr.due_date,
            success_criteria=okr.success_criteria, assigned_by=okr.assigned_by,
            evidence_url=okr.evidence_url, completion_remarks=okr.completion_remarks,
            appraisal_submitted=okr.appraisal_submitted, appraisal_summary=okr.appraisal_summary,
            appraisal_evidence=okr.appraisal_evidence, previous_ctc=okr.previous_ctc,
            current_ctc=okr.current_ctc, appraisal_percentage=okr.appraisal_percentage,
            employee_name=emp.full_name if emp else "Unknown"
        ))
    return results

@router.post("/", response_model=schemas.OKROut)
def create_appraisal(okr_in: schemas.OKRCreate, db: Session = Depends(get_db)):
    emp = db.query(models.Employee).filter(models.Employee.id == okr_in.employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    db_okr = models.OKR(
        employee_id=okr_in.employee_id, type=okr_in.type, objective=okr_in.objective,
        key_results=okr_in.key_results, progress=okr_in.progress or 0.0,
        year=okr_in.year, quarter=okr_in.quarter, due_date=okr_in.due_date,
        success_criteria=okr_in.success_criteria, assigned_by=okr_in.assigned_by,
        appraisal_submitted=False
    )
    db.add(db_okr)
    db.commit()
    db.refresh(db_okr)

    return schemas.OKROut(
        id=db_okr.id, employee_id=db_okr.employee_id, type=db_okr.type,
        objective=db_okr.objective, key_results=db_okr.key_results,
        progress=float(db_okr.progress) if db_okr.progress is not None else 0.0,
        year=db_okr.year, quarter=db_okr.quarter, due_date=db_okr.due_date,
        success_criteria=db_okr.success_criteria, assigned_by=db_okr.assigned_by,
        employee_name=emp.full_name
    )

@router.put("/{id}", response_model=schemas.OKROut)
def update_appraisal(id: int, okr_in: schemas.OKRUpdate, db: Session = Depends(get_db)):
    okr = db.query(models.OKR).filter(models.OKR.id == id).first()
    if not okr:
        raise HTTPException(status_code=404, detail="OKR not found")

    update_data = okr_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(okr, field, value)

    if "current_ctc" in update_data and update_data["current_ctc"] is not None:
        emp = db.query(models.Employee).filter(models.Employee.id == okr.employee_id).first()
        if emp:
            emp.salary = update_data["current_ctc"]

    db.commit()
    db.refresh(okr)

    emp = db.query(models.Employee).filter(models.Employee.id == okr.employee_id).first()
    return schemas.OKROut(
        id=okr.id, employee_id=okr.employee_id, type=okr.type,
        objective=okr.objective, key_results=okr.key_results,
        progress=float(okr.progress) if okr.progress is not None else 0.0,
        year=okr.year, quarter=okr.quarter, due_date=okr.due_date,
        success_criteria=okr.success_criteria, assigned_by=okr.assigned_by,
        evidence_url=okr.evidence_url, completion_remarks=okr.completion_remarks,
        appraisal_submitted=okr.appraisal_submitted, appraisal_summary=okr.appraisal_summary,
        appraisal_evidence=okr.appraisal_evidence, previous_ctc=okr.previous_ctc,
        current_ctc=okr.current_ctc, appraisal_percentage=okr.appraisal_percentage,
        employee_name=emp.full_name if emp else "Unknown"
    )

@router.delete("/{id}")
def delete_appraisal(id: int, db: Session = Depends(get_db)):
    okr = db.query(models.OKR).filter(models.OKR.id == id).first()
    if not okr:
        raise HTTPException(status_code=404, detail="OKR not found")
    db.delete(okr)
    db.commit()
    return {"message": "OKR deleted successfully"}
