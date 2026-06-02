from fastapi import APIRouter
from database import mock_db

router = APIRouter(prefix="/holidays", tags=["holidays"])

@router.get("/list")
def get_holidays():
    """
    Get the list of upcoming holidays.
    """
    return mock_db.holidays
