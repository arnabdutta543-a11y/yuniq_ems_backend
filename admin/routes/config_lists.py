from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from admin.database import get_db
from admin import models, schemas

router = APIRouter(tags=["Admin Configuration Lists"])

# --- Roles Endpoints ---
@router.get("/roles", response_model=List[schemas.RoleOut])
def get_roles(db: Session = Depends(get_db)):
    return db.query(models.Role).order_by(models.Role.name.asc()).all()

@router.post("/roles", response_model=schemas.RoleOut)
def create_role(role_in: schemas.RoleCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Role).filter(models.Role.name.ilike(role_in.name)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Role already exists.")
    db_role = models.Role(name=role_in.name)
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role

@router.delete("/roles/{id}")
def delete_role(id: int, db: Session = Depends(get_db)):
    role = db.query(models.Role).filter(models.Role.id == id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found.")
    db.delete(role)
    db.commit()
    return {"message": "Role successfully deleted."}


# --- Departments Endpoints ---
@router.get("/departments", response_model=List[schemas.DepartmentOut])
def get_departments(db: Session = Depends(get_db)):
    return db.query(models.Department).order_by(models.Department.name.asc()).all()

@router.post("/departments", response_model=schemas.DepartmentOut)
def create_department(dept_in: schemas.DepartmentCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Department).filter(models.Department.name.ilike(dept_in.name)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Department already exists.")
    db_dept = models.Department(name=dept_in.name)
    db.add(db_dept)
    db.commit()
    db.refresh(db_dept)
    return db_dept

@router.delete("/departments/{id}")
def delete_department(id: int, db: Session = Depends(get_db)):
    dept = db.query(models.Department).filter(models.Department.id == id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found.")
    db.delete(dept)
    db.commit()
    return {"message": "Department successfully deleted."}


# --- Offices Endpoints ---
@router.get("/offices", response_model=List[schemas.OfficeOut])
def get_offices(db: Session = Depends(get_db)):
    return db.query(models.Office).order_by(models.Office.name.asc()).all()

@router.post("/offices", response_model=schemas.OfficeOut)
def create_office(office_in: schemas.OfficeCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Office).filter(models.Office.name.ilike(office_in.name)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Office location already exists.")
    db_office = models.Office(name=office_in.name)
    db.add(db_office)
    db.commit()
    db.refresh(db_office)
    return db_office

@router.delete("/offices/{id}")
def delete_office(id: int, db: Session = Depends(get_db)):
    office = db.query(models.Office).filter(models.Office.id == id).first()
    if not office:
        raise HTTPException(status_code=404, detail="Office not found.")
    db.delete(office)
    db.commit()
    return {"message": "Office location successfully deleted."}
