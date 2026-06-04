from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from config import settings
from database import init_db
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

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    print("Starting up YuniQ Portal API...")
    init_db()
    yield
    # Shutdown actions
    print("Shutting down YuniQ Portal API...")

app = FastAPI(
    title=settings.APP_NAME,
    description="Replica & Extension of YuniQ Employee Portal backend",
    version="1.0.0",
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

from fastapi.staticfiles import StaticFiles
import os
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include Routers
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

@app.get("/")
def read_root():
    return {
        "status": "online",
        "app_name": settings.APP_NAME,
        "mock_mode": settings.is_mock_mode
    }
