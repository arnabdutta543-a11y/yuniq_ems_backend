from fastapi import APIRouter
from database import mock_db

router = APIRouter(prefix="/policy", tags=["policy"])

@router.get("/list")
def get_policies():
    """
    List company policies.
    """
    return mock_db.policies
