from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import List, Optional, Any
from database import mock_db, get_db, TravelRequestDB, NotificationDB
from routers.auth import get_current_user_id
from redis_cache import cache_service
import serpapi_client
import datetime

router = APIRouter(prefix="/travel", tags=["travel"])

class BookTravelRequest(BaseModel):
    destination: str
    departure_date: str
    return_date: str
    selected_flight: Optional[Any] = None
    selected_hotel: Optional[Any] = None

@router.get("/flights")
def get_flights(
    departure: str = Query(..., description="Departure airport code (e.g. BOM)"),
    arrival: str = Query(..., description="Arrival airport code (e.g. SFO)"),
    date: str = Query(..., description="Departure date (YYYY-MM-DD)"),
    user_id: str = Depends(get_current_user_id)
):
    cache_key = f"flights:{departure}:{arrival}:{date}"
    cached_data = cache_service.get(cache_key)
    if cached_data:
        print(f"Returning cached flights for: {cache_key}")
        return cached_data
        
    flights = serpapi_client.search_flights(departure, arrival, date)
    cache_service.set(cache_key, flights, expire_seconds=3600)
    return flights

@router.get("/hotels")
def get_hotels(
    location: str = Query(..., description="Location to search hotels (e.g. San Francisco)"),
    check_in: str = Query(..., description="Check-in date (YYYY-MM-DD)"),
    check_out: str = Query(..., description="Check-out date (YYYY-MM-DD)"),
    user_id: str = Depends(get_current_user_id)
):
    cache_key = f"hotels:{location}:{check_in}:{check_out}"
    cached_data = cache_service.get(cache_key)
    if cached_data:
        print(f"Returning cached hotels for: {cache_key}")
        return cached_data
        
    hotels = serpapi_client.search_hotels(location, check_in, check_out)
    cache_service.set(cache_key, hotels, expire_seconds=3600)
    return hotels

@router.get("/requests")
def get_travel_requests(user_id: str = Depends(get_current_user_id), db = Depends(get_db)):
    if db:
        req_records = db.query(TravelRequestDB).filter(TravelRequestDB.user_id == user_id).all()
        return [{
            "id": r.id,
            "user_id": r.user_id,
            "destination": r.destination,
            "departure_date": r.departure_date.isoformat(),
            "return_date": r.return_date.isoformat(),
            "status": r.status,
            "selected_flight": r.selected_flight,
            "selected_hotel": r.selected_hotel
        } for r in req_records]
        
    # Fallback to mock DB
    requests = [r for r in mock_db.travel_requests if r["user_id"] == user_id]
    return requests

@router.post("/book")
def book_travel(data: BookTravelRequest, user_id: str = Depends(get_current_user_id), db = Depends(get_db)):
    now_str = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
    try:
        dep_date = datetime.date.fromisoformat(data.departure_date)
        ret_date = datetime.date.fromisoformat(data.return_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format (use YYYY-MM-DD)")
        
    if db:
        new_request = TravelRequestDB(
            id=f"travel-{int(datetime.datetime.now().timestamp())}",
            user_id=user_id,
            destination=data.destination,
            departure_date=dep_date,
            return_date=ret_date,
            status="Pending Approval",
            selected_flight=data.selected_flight,
            selected_hotel=data.selected_hotel
        )
        db.add(new_request)
        
        # Add Notification
        new_notif = NotificationDB(
            id=f"notif-{int(datetime.datetime.now().timestamp())}",
            user_id=user_id,
            title="Travel Request Submitted",
            message=f"Your travel request to {data.destination} has been submitted for approval.",
            read=False,
            created_at=now_str
        )
        db.add(new_notif)
        db.commit()
        return {"message": "Travel request submitted successfully"}
        
    # Fallback to mock DB
    new_request = {
        "id": f"travel-{len(mock_db.travel_requests) + 1}",
        "user_id": user_id,
        "destination": data.destination,
        "departure_date": data.departure_date,
        "return_date": data.return_date,
        "status": "Pending Approval",
        "selected_flight": data.selected_flight,
        "selected_hotel": data.selected_hotel
    }
    mock_db.travel_requests.append(new_request)
    mock_db.notifications.append({
        "id": f"notif-{len(mock_db.notifications) + 1}",
        "user_id": user_id,
        "title": "Travel Request Submitted",
        "message": f"Your travel request to {data.destination} has been submitted for approval.",
        "read": False,
        "created_at": now_str
    })
    return {"message": "Travel request submitted successfully", "request": new_request}
