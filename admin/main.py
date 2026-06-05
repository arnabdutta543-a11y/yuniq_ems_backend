import os
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from .database import engine, Base, get_db
from . import models, schemas
from .routes import auth, config_lists, employees, leaves, timesheets, travel, performance, holidays, payslips, resources, recognitions, trainings, asset_requests, announcements, policies, appraisals

# Initialize database schemas
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="YuniQ EMS Admin Portal API",
    description="Backend services for administering employees, leaves, timesheets, travel requests, and performance evaluations.",
    version="1.1.0"
)

# Mount static files directory relative to main.py
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# CORS configurations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(config_lists.router, prefix="/api")
app.include_router(employees.router, prefix="/api")
app.include_router(leaves.router, prefix="/api")
app.include_router(timesheets.router, prefix="/api")
app.include_router(travel.router, prefix="/api")
app.include_router(performance.router, prefix="/api")
app.include_router(holidays.router, prefix="/api")
app.include_router(payslips.router, prefix="/api")
app.include_router(resources.router, prefix="/api")
app.include_router(recognitions.router, prefix="/api")
app.include_router(trainings.router, prefix="/api")
app.include_router(asset_requests.router, prefix="/api")
app.include_router(announcements.router, prefix="/api")
app.include_router(policies.router, prefix="/api")
app.include_router(appraisals.router, prefix="/api")

@app.get("/api")
def api_root():
    return {
        "status": "online",
        "service": "YuniQ EMS Admin API Portal",
        "version": "1.1.0"
    }

@app.get("/api/stats", response_model=schemas.DashboardStatsOut)
def get_dashboard_stats(db: Session = Depends(get_db)):
    # Calculate key administrative operational metrics
    total_employees = db.query(models.Employee).count()
    
    total_managers = db.query(models.Employee).filter(
        models.Employee.role.in_(["Director", "Manager", "CEO", "Senior Manager", "HR Manager", "Management"])
    ).count()

    total_hrs = db.query(models.Employee).filter(
        models.Employee.role == "HR Manager"
    ).count()

    pending_onboardings = db.query(models.Employee).filter(
        models.Employee.status == "Pending"
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
