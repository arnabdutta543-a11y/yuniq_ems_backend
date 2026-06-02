from fastapi import APIRouter, Depends
from database import mock_db, get_db, PolicyDB

router = APIRouter(prefix="/policy", tags=["policy"])

@router.get("/list")
def get_policies(db = Depends(get_db)):
    """
    List company policies.
    """
    if db:
        policies_records = db.query(PolicyDB).all()
        return [{
            "id": p.id,
            "title": p.title,
            "category": p.category,
            "url": p.url,
            "published_at": p.published_at.isoformat()
        } for p in policies_records]
        
    return mock_db.policies
