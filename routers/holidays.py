from fastapi import APIRouter, Depends
from database import mock_db, get_db, HolidayDB

router = APIRouter(prefix="/holidays", tags=["holidays"])

@router.get("/list")
def get_holidays(db = Depends(get_db)):
    """
    Get the list of upcoming holidays.
    """
    if db:
        holidays_records = db.query(HolidayDB).order_by(HolidayDB.date.asc()).all()
        return [{
            "id": h.id,
            "name": h.name,
            "date": h.date.isoformat(),
            "day": h.day
        } for h in holidays_records]
        
    return mock_db.holidays
