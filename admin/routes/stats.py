from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from admin.database import get_db
from admin import models, schemas

router = APIRouter(tags=["Admin Dashboard"])

@router.get("/stats", response_model=schemas.DashboardStatsOut)
def get_dashboard_stats(db: Session = Depends(get_db)):
    total_employees = db.query(models.Employee).filter(models.Employee.status == "Active").count()
    total_managers = db.query(models.Employee).filter(
        models.Employee.role.in_([
            "Director", "Manager", "CEO", "Senior Manager", "HR Manager", "Management"
        ]),
        models.Employee.status == "Active"
    ).count()
    total_hrs = db.query(models.Employee).filter(
        models.Employee.role.ilike("%hr%"),
        models.Employee.status == "Active"
    ).count()
    pending_onboardings = db.query(models.OnboardingInvitation).filter(
        models.OnboardingInvitation.used == False
    ).count()
    active_leaves = db.query(models.Leave).filter(
        models.Leave.status == "Pending"
    ).count()
    timesheets_pending = db.query(models.Timesheet).filter(
        models.Timesheet.status == "Submitted"
    ).count()

    return schemas.DashboardStatsOut(
        total_employees=total_employees,
        total_managers=total_managers,
        total_hrs=total_hrs,
        pending_onboardings=pending_onboardings,
        active_leaves=active_leaves,
        timesheets_pending=timesheets_pending
    )
