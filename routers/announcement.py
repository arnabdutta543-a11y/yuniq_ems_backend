from fastapi import APIRouter, Depends
from database import mock_db, get_db, AnnouncementDB, KnowledgeBaseDB

router = APIRouter(prefix="/announcements", tags=["announcements"])

@router.get("/list")
def get_announcements(db = Depends(get_db)):
    if db:
        anns = db.query(AnnouncementDB).order_by(AnnouncementDB.created_at.desc()).all()
        return [{
            "id": a.id,
            "title": a.title,
            "content": a.content,
            "category": a.category,
            "created_at": a.created_at.isoformat()
        } for a in anns]
        
    return mock_db.announcements

@router.get("/knowledge-base")
def get_knowledge_base(db = Depends(get_db)):
    if db:
        kb_items = db.query(KnowledgeBaseDB).all()
        return [{
            "id": k.id,
            "title": k.title,
            "category": k.category,
            "content": k.content,
            "url": k.url
        } for k in kb_items]
        
    return mock_db.knowledge_base
