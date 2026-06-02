from fastapi import APIRouter, HTTPException, Depends
from typing import List
from database import mock_db
from routers.auth import get_current_user_id

router = APIRouter(prefix="/profile", tags=["profile"])

@router.get("/me")
def get_my_profile(user_id: str = Depends(get_current_user_id)):
    profile = next((p for p in mock_db.profiles if p["id"] == user_id), None)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

@router.get("/teams")
def get_reporting_team(user_id: str = Depends(get_current_user_id)):
    """
    Dynamically generates the team hierarchy for the logged in user.
    Returns the manager and all members under that manager.
    """
    user_profile = next((p for p in mock_db.profiles if p["id"] == user_id), None)
    if not user_profile:
        raise HTTPException(status_code=404, detail="Profile not found")
        
    manager_id = user_profile["manager_id"]
    manager_profile = None
    if manager_id:
        manager_profile = next((p for p in mock_db.profiles if p["id"] == manager_id), None)
        
    # Get all profiles who report to the same manager (teammates/peers)
    peers = []
    if manager_id:
        peers = [p for p in mock_db.profiles if p["manager_id"] == manager_id]
    else:
        # If user has no manager, they are at the top; find who reports to them
        peers = [p for p in mock_db.profiles if p["manager_id"] == user_id]
        
    return {
        "user": user_profile,
        "manager": manager_profile,
        "teammates": peers
    }

@router.get("/{profile_id}")
def get_profile_by_id(profile_id: str):
    profile = next((p for p in mock_db.profiles if p["id"] == profile_id), None)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile
