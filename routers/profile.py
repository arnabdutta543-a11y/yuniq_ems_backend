from fastapi import APIRouter, HTTPException, Depends
from typing import List
from database import mock_db, get_db, ProfileDB
from routers.auth import get_current_user_id

router = APIRouter(prefix="/profile", tags=["profile"])

def serialize_profile(p: ProfileDB) -> dict:
    return {
        "id": p.id,
        "full_name": p.full_name,
        "email": p.email,
        "role": p.role,
        "department": p.department,
        "manager_id": p.manager_id,
        "avatar_url": p.avatar_url
    }

@router.get("/me")
def get_my_profile(user_id: str = Depends(get_current_user_id), db = Depends(get_db)):
    if db:
        p = db.query(ProfileDB).filter(ProfileDB.id == user_id).first()
        if p:
            return serialize_profile(p)
            
    profile = next((p for p in mock_db.profiles if p["id"] == user_id), None)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

@router.get("/teams")
def get_reporting_team(user_id: str = Depends(get_current_user_id), db = Depends(get_db)):
    """
    Dynamically generates the team hierarchy for the logged in user.
    """
    if db:
        user_p = db.query(ProfileDB).filter(ProfileDB.id == user_id).first()
        if not user_p:
            raise HTTPException(status_code=404, detail="Profile not found")
            
        manager_id = user_p.manager_id
        manager_p = None
        if manager_id:
            manager_record = db.query(ProfileDB).filter(ProfileDB.id == manager_id).first()
            if manager_record:
                manager_p = serialize_profile(manager_record)
                
        # Find peers (profiles sharing the same manager)
        peers_records = []
        if manager_id:
            peers_records = db.query(ProfileDB).filter(ProfileDB.manager_id == manager_id).all()
        else:
            peers_records = db.query(ProfileDB).filter(ProfileDB.manager_id == user_id).all()
            
        return {
            "user": serialize_profile(user_p),
            "manager": manager_p,
            "teammates": [serialize_profile(peer) for peer in peers_records]
        }
        
    # Fallback to mock DB
    user_profile = next((p for p in mock_db.profiles if p["id"] == user_id), None)
    if not user_profile:
        raise HTTPException(status_code=404, detail="Profile not found")
        
    manager_id = user_profile["manager_id"]
    manager_profile = None
    if manager_id:
        manager_profile = next((p for p in mock_db.profiles if p["id"] == manager_id), None)
        
    peers = []
    if manager_id:
        peers = [p for p in mock_db.profiles if p["manager_id"] == manager_id]
    else:
        peers = [p for p in mock_db.profiles if p["manager_id"] == user_id]
        
    return {
        "user": user_profile,
        "manager": manager_profile,
        "teammates": peers
    }

@router.get("/{profile_id}")
def get_profile_by_id(profile_id: str, db = Depends(get_db)):
    if db:
        p = db.query(ProfileDB).filter(ProfileDB.id == profile_id).first()
        if p:
            return serialize_profile(p)
            
    profile = next((p for p in mock_db.profiles if p["id"] == profile_id), None)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile
