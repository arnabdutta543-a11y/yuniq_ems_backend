from fastapi import APIRouter, Depends
from database import mock_db, get_db, HolidayDB, ProfileDB
from routers.auth import get_current_user_id

router = APIRouter(prefix="/holidays", tags=["holidays"])

@router.get("/list")
def get_holidays(user_id: str = Depends(get_current_user_id), db = Depends(get_db)):
    """
    Get the list of upcoming holidays matched to the employee's location.
    """
    if db:
        emp = db.query(ProfileDB).filter(ProfileDB.id == user_id).first()
        location = emp.office if emp else "All"
        if not location:
            location = "All"
            
        holidays_records = db.query(HolidayDB).filter(
            (HolidayDB.location == 'All') | (HolidayDB.location.ilike(location))
        ).order_by(HolidayDB.date.asc()).all()
        
        return [{
            "id": h.id,
            "name": h.name,
            "date": h.date.isoformat(),
            "day": h.day,
            "location": h.location,
            "type": h.type
        } for h in holidays_records]
        
    return mock_db.holidays
