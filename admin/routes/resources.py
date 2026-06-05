from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from admin.database import get_db
from admin import models, schemas

router = APIRouter(prefix="/resources", tags=["Admin Resources"])

def _build_out(r: models.Resource, emp_name: Optional[str]) -> schemas.ResourceOut:
    return schemas.ResourceOut(
        id=r.id, name=r.name, asset_id=r.asset_id,
        serial_number=r.serial_number, specifications=r.specifications,
        employee_id=r.employee_id, status=r.status, employee_name=emp_name
    )

@router.get("/", response_model=List[schemas.ResourceOut])
def get_resources(db: Session = Depends(get_db)):
    resources = db.query(models.Resource).all()
    res_out = []
    for r in resources:
        emp_name = None
        if r.employee_id:
            emp = db.query(models.Employee).filter(models.Employee.id == r.employee_id).first()
            if emp:
                emp_name = emp.full_name
        res_out.append(_build_out(r, emp_name))
    return res_out

@router.post("/", response_model=schemas.ResourceOut)
def create_resource(res_in: schemas.ResourceCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Resource).filter(
        models.Resource.asset_id == res_in.asset_id.strip()
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resource with this Asset ID already exists"
        )

    status_val = "Available"
    if res_in.employee_id:
        status_val = "Allocated"
        if res_in.name.lower() == "laptop":
            emp = db.query(models.Employee).filter(models.Employee.id == res_in.employee_id).first()
            if emp:
                emp.assigned_laptop = res_in.asset_id

    db_resource = models.Resource(
        name=res_in.name, asset_id=res_in.asset_id.strip(),
        serial_number=res_in.serial_number.strip() if res_in.serial_number else None,
        specifications=res_in.specifications, employee_id=res_in.employee_id,
        status=status_val
    )
    db.add(db_resource)
    db.commit()
    db.refresh(db_resource)

    emp_name = None
    if db_resource.employee_id:
        emp = db.query(models.Employee).filter(models.Employee.id == db_resource.employee_id).first()
        if emp:
            emp_name = emp.full_name

    return _build_out(db_resource, emp_name)

@router.put("/{id}", response_model=schemas.ResourceOut)
def update_resource(id: int, res_in: schemas.ResourceUpdate, db: Session = Depends(get_db)):
    resource = db.query(models.Resource).filter(models.Resource.id == id).first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    update_data = res_in.model_dump(exclude_unset=True)

    if "employee_id" in update_data:
        new_emp_id = update_data["employee_id"]
        old_emp_id = resource.employee_id

        if new_emp_id != old_emp_id:
            if resource.name.lower() == "laptop" and old_emp_id:
                old_emp = db.query(models.Employee).filter(models.Employee.id == old_emp_id).first()
                if old_emp and old_emp.assigned_laptop == resource.asset_id:
                    old_emp.assigned_laptop = None

            if resource.name.lower() == "laptop" and new_emp_id:
                new_emp = db.query(models.Employee).filter(models.Employee.id == new_emp_id).first()
                if new_emp:
                    new_emp.assigned_laptop = resource.asset_id

            resource.employee_id = new_emp_id
            resource.status = "Allocated" if new_emp_id else "Available"

    for field, value in update_data.items():
        if field != "employee_id":
            setattr(resource, field, value)

    db.commit()
    db.refresh(resource)

    emp_name = None
    if resource.employee_id:
        emp = db.query(models.Employee).filter(models.Employee.id == resource.employee_id).first()
        if emp:
            emp_name = emp.full_name

    return _build_out(resource, emp_name)

@router.delete("/{id}", response_model=schemas.ResourceOut)
def delete_resource(id: int, db: Session = Depends(get_db)):
    resource = db.query(models.Resource).filter(models.Resource.id == id).first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    if resource.name.lower() == "laptop" and resource.employee_id:
        emp = db.query(models.Employee).filter(models.Employee.id == resource.employee_id).first()
        if emp and emp.assigned_laptop == resource.asset_id:
            emp.assigned_laptop = None

    out = _build_out(resource, None)
    db.delete(resource)
    db.commit()
    return out
