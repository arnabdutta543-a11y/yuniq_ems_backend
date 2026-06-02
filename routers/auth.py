from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from jose import JWTError, jwt
from typing import Optional
from database import mock_db
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
        # In mock mode, default to debarati if no token is passed
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
def login(data: LoginRequest):
    email = data.email.lower().strip()
    
    # Authenticate profile (in mock db, any password works for our mock profiles)
    profile = None
    for p in mock_db.profiles:
        if p["email"].lower() == email:
            profile = p
            break
            
    if not profile:
        # If user not found, default to Debarati Patra for ease of testing
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
def get_me(user_id: str = Depends(get_current_user_id)):
    profile = next((p for p in mock_db.profiles if p["id"] == user_id), None)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile
