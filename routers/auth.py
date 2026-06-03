from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from jose import JWTError, jwt
from typing import Optional
from database import mock_db, get_db, ProfileDB
import datetime

router = APIRouter(prefix="/auth", tags=["auth"])

SECRET_KEY = "yuniq-secret-key-for-jwt-tokens"
ALGORITHM = "HS256"

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    profile: dict

def get_current_user_id(authorization: Optional[str] = Header(None)) -> str:
    """
    Dependency to get the authenticated user_id.
    """
    if not authorization or not authorization.startswith("Bearer "):
        return "user-debarati"
    
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authorization token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

@router.post("/login", response_model=LoginResponse)
def login(data: LoginRequest, db = Depends(get_db)):
    email = data.email.lower().strip()
    
    profile = None
    if db:
        prof_record = db.query(ProfileDB).filter(ProfileDB.email.ilike(email)).first()
        if prof_record:
            from routers.profile import serialize_profile
            profile = serialize_profile(prof_record)
            
    if not profile:
        # Fallback to mock db search
        for p in mock_db.profiles:
            if p["email"].lower() == email:
                profile = p
                break
            
    if not profile:
        # Default to Debarati Patra for ease of testing
        profile = next(p for p in mock_db.profiles if p["id"] == "user-debarati")
        
    # Generate JWT Token
    expire = datetime.datetime.utcnow() + datetime.timedelta(days=1)
    payload = {
        "sub": profile["id"],
        "email": profile["email"],
        "exp": expire
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "profile": profile
    }

@router.get("/me")
def get_me(user_id: str = Depends(get_current_user_id), db = Depends(get_db)):
    if db:
        prof_record = db.query(ProfileDB).filter(ProfileDB.id == user_id).first()
        if prof_record:
            from routers.profile import serialize_profile
            return serialize_profile(prof_record)
            
    profile = next((p for p in mock_db.profiles if p["id"] == user_id), None)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile
