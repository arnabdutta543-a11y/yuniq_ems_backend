from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
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

app = FastAPI(
    title=settings.APP_NAME,
    description="Replica & Extension of YuniQ Employee Portal backend",
    version="1.0.0",
    debug=settings.DEBUG
)

# Configure CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In development we allow all; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.get("/")
def read_root():
    return {
        "status": "online",
        "app_name": settings.APP_NAME,
        "mock_mode": settings.is_mock_mode
    }
