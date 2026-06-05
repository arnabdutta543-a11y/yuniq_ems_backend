from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from config import settings
from database import init_db
from admin.auth_deps import admin_access_required

# ── EMS Routers ────────────────────────────────────────────────────────────────
import routers.auth
import routers.profile
import routers.attendance
import routers.timesheet
import routers.leave
import routers.feedback
import routers.travel
import routers.policy
import routers.holidays
import routers.notifications
import routers.okr
import routers.recognition
import routers.training
import routers.payroll
import routers.asset
import routers.announcement
import routers.ai_analyzer
import routers.upload

# ── Admin Routers ──────────────────────────────────────────────────────────────
from admin.routes.auth import router as admin_auth_router
from admin.routes.config_lists import router as admin_config_router
from admin.routes.employees import router as admin_employees_router
from admin.routes.announcements import router as admin_announcements_router
from admin.routes.appraisals import router as admin_appraisals_router
from admin.routes.asset_requests import router as admin_asset_requests_router
from admin.routes.holidays import router as admin_holidays_router
from admin.routes.leaves import router as admin_leaves_router
from admin.routes.payslips import router as admin_payslips_router
from admin.routes.performance import router as admin_performance_router
from admin.routes.policies import router as admin_policies_router
from admin.routes.recognitions import router as admin_recognitions_router
from admin.routes.resources import router as admin_resources_router
from admin.routes.timesheets import router as admin_timesheets_router
from admin.routes.trainings import router as admin_trainings_router
from admin.routes.travel import router as admin_travel_router
from admin.routes.stats import router as admin_stats_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup — initialize EMS DB tables
    print("Starting up YuniQ Unified Portal API (EMS + Admin)...")
    init_db()

    # Initialize Admin DB tables (same DB, separate SQLAlchemy Base)
    try:
        from admin.database import Base, admin_engine
        Base.metadata.create_all(bind=admin_engine)
        print("Admin DB tables verified / created successfully.")
    except Exception as e:
        print(f"Warning: Admin DB initialization encountered an issue: {e}")

    yield
    print("Shutting down YuniQ Unified Portal API...")


app = FastAPI(
    title="YuniQ Unified Portal API",
    description=(
        "Unified backend for the YuniQ Employee Management System (EMS) and Admin Portal. "
        "EMS routes are served at /api/* and Admin routes at /api/admin/*."
    ),
    version="2.0.0",
    debug=settings.DEBUG,
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static file mounts ─────────────────────────────────────────────────────────
import os
from fastapi.staticfiles import StaticFiles

os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

os.makedirs(os.path.join("static", "policies"), exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# ── EMS Routers  (prefix: /api/*) ─────────────────────────────────────────────
app.include_router(routers.auth.router, prefix="/api")
app.include_router(routers.profile.router, prefix="/api")
app.include_router(routers.attendance.router, prefix="/api")
app.include_router(routers.timesheet.router, prefix="/api")
app.include_router(routers.leave.router, prefix="/api")
app.include_router(routers.feedback.router, prefix="/api")
app.include_router(routers.travel.router, prefix="/api")
app.include_router(routers.policy.router, prefix="/api")
app.include_router(routers.holidays.router, prefix="/api")
app.include_router(routers.notifications.router, prefix="/api")
app.include_router(routers.okr.router, prefix="/api")
app.include_router(routers.recognition.router, prefix="/api")
app.include_router(routers.training.router, prefix="/api")
app.include_router(routers.payroll.router, prefix="/api")
app.include_router(routers.asset.router, prefix="/api")
app.include_router(routers.announcement.router, prefix="/api")
app.include_router(routers.ai_analyzer.router, prefix="/api")
app.include_router(routers.upload.router, prefix="/api")

# ── Admin Routers  (prefix: /api/admin/*) ─────────────────────────────────────
ADMIN_PREFIX = "/api/admin"
app.include_router(admin_auth_router,          prefix=ADMIN_PREFIX)
app.include_router(admin_config_router,        prefix=ADMIN_PREFIX, dependencies=[Depends(admin_access_required)])
app.include_router(admin_employees_router,     prefix=ADMIN_PREFIX, dependencies=[Depends(admin_access_required)])
app.include_router(admin_announcements_router, prefix=ADMIN_PREFIX, dependencies=[Depends(admin_access_required)])
app.include_router(admin_appraisals_router,    prefix=ADMIN_PREFIX, dependencies=[Depends(admin_access_required)])
app.include_router(admin_asset_requests_router,prefix=ADMIN_PREFIX, dependencies=[Depends(admin_access_required)])
app.include_router(admin_holidays_router,      prefix=ADMIN_PREFIX, dependencies=[Depends(admin_access_required)])
app.include_router(admin_leaves_router,        prefix=ADMIN_PREFIX, dependencies=[Depends(admin_access_required)])
app.include_router(admin_payslips_router,      prefix=ADMIN_PREFIX, dependencies=[Depends(admin_access_required)])
app.include_router(admin_performance_router,   prefix=ADMIN_PREFIX, dependencies=[Depends(admin_access_required)])
app.include_router(admin_policies_router,      prefix=ADMIN_PREFIX, dependencies=[Depends(admin_access_required)])
app.include_router(admin_recognitions_router,  prefix=ADMIN_PREFIX, dependencies=[Depends(admin_access_required)])
app.include_router(admin_resources_router,     prefix=ADMIN_PREFIX, dependencies=[Depends(admin_access_required)])
app.include_router(admin_timesheets_router,    prefix=ADMIN_PREFIX, dependencies=[Depends(admin_access_required)])
app.include_router(admin_trainings_router,     prefix=ADMIN_PREFIX, dependencies=[Depends(admin_access_required)])
app.include_router(admin_travel_router,        prefix=ADMIN_PREFIX, dependencies=[Depends(admin_access_required)])
app.include_router(admin_stats_router,         prefix=ADMIN_PREFIX, dependencies=[Depends(admin_access_required)])


@app.get("/")
def read_root():
    return {
        "status": "online",
        "app_name": "YuniQ Unified Portal API",
        "version": "2.0.0",
        "portals": {
            "ems_employee_portal": "/api/",
            "admin_portal": "/api/admin/"
        },
        "docs": "/docs",
        "mock_mode": settings.is_mock_mode
    }


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "YuniQ Unified Backend"}

