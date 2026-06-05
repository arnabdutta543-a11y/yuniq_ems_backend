from fastapi import Header, HTTPException, Depends, status
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from admin.database import get_db
from admin.models import Employee
from typing import Optional

SECRET_KEY = "yuniq-secret-key-for-jwt-tokens"
ALGORITHM = "HS256"

def admin_access_required(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Dependency to verify that the request is authenticated and the user has admin access.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header."
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Use 'Bearer <token>'."
        )
    
    token = authorization.split(" ")[1]
    
    # Handle mock tokens
    if token.startswith("mock-jwt-token-"):
        user_id = token.replace("mock-jwt-token-", "")
    elif token == "mock-admin-token":
        return "admin-yuniq" # Global Admin bypass
    elif token == "mock-jwt-token":
        user_id = "user-debarati" # Mock EMS default user
    else:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: str = payload.get("sub")
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authorization token."
                )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials."
            )
            
    # Allow global admin bypass directly
    if user_id == "admin-yuniq":
        return user_id

    # Query database to check if user exists and has admin portal access
    user = db.query(Employee).filter(Employee.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user profile not found."
        )
        
    if not user.admin_portal_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Admin portal access required."
        )
        
    return user_id
