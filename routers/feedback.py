from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from database import mock_db, get_db, FeedbackDB, ProfileDB, PromotionDB
from routers.auth import get_current_user_id

router = APIRouter(prefix="/feedback", tags=["feedback"])

class SubmitFeedbackRequest(BaseModel):
    reviewer_id: str
    feedback_type: str # manager/peer
    year: int
    rating_work_quality: int
    rating_collaboration: int
    rating_leadership: int
    comments: str
    project_ratings: Dict[str, float]

@router.get("/performance")
def get_performance_report(user_id: str = Depends(get_current_user_id), year: int = 2025, db = Depends(get_db)):
    """
    Get aggregated performance stats, reviews, and promotion timeline for a given year.
    """
    if db:
        reviews = db.query(FeedbackDB).filter(FeedbackDB.user_id == user_id, FeedbackDB.year == year).all()
        
        # Calculate averages
        avg_quality = 0.0
        avg_collab = 0.0
        avg_lead = 0.0
        
        if reviews:
            avg_quality = sum(f.rating_work_quality for f in reviews) / len(reviews)
            avg_collab = sum(f.rating_collaboration for f in reviews) / len(reviews)
            avg_lead = sum(f.rating_leadership for f in reviews) / len(reviews)
            
        project_ratings_map = {}
        for f in reviews:
            for proj, rating in (f.project_ratings or {}).items():
                if proj not in project_ratings_map:
                    project_ratings_map[proj] = []
                project_ratings_map[proj].append(rating)
                
        project_summary = []
        for proj, ratings in project_ratings_map.items():
            project_summary.append({
                "project_name": proj,
                "average_rating": round(sum(ratings) / len(ratings), 2),
                "reviews_count": len(ratings)
            })
            
        # Get promotions
        promotions_records = db.query(PromotionDB).filter(PromotionDB.user_id == user_id).all()
        promotions_list = [{
            "id": p.id,
            "old_role": p.old_role,
            "new_role": p.new_role,
            "date": p.date.isoformat(),
            "details": p.details
        } for p in promotions_records]
        
        detailed_feedbacks = []
        for f in reviews:
            reviewer = db.query(ProfileDB).filter(ProfileDB.id == f.reviewer_id).first()
            detailed_feedbacks.append({
                "id": f.id,
                "reviewer_name": reviewer.full_name if reviewer else "Anonymous Teammate",
                "reviewer_role": reviewer.role if reviewer else "Teammate",
                "type": f.feedback_type,
                "comments": f.comments,
                "ratings": {
                    "quality": f.rating_work_quality,
                    "collaboration": f.rating_collaboration,
                    "leadership": f.rating_leadership
                }
            })
            
        return {
            "year": year,
            "averages": {
                "work_quality": round(avg_quality, 2),
                "collaboration": round(avg_collab, 2),
                "leadership": round(avg_lead, 2)
            },
            "project_details": project_summary,
            "feedbacks": detailed_feedbacks,
            "promotions": promotions_list
        }
        
    # Fallback to mock DB
    reviews = [fb for fb in mock_db.feedbacks if fb["user_id"] == user_id and fb["year"] == year]
    avg_quality = 0.0
    avg_collab = 0.0
    avg_lead = 0.0
    
    if reviews:
        avg_quality = sum(fb["rating_work_quality"] for fb in reviews) / len(reviews)
        avg_collab = sum(fb["rating_collaboration"] for fb in reviews) / len(reviews)
        avg_lead = sum(fb["rating_leadership"] for fb in reviews) / len(reviews)
        
    project_ratings_map = {}
    for fb in reviews:
        for proj, rating in fb.get("project_ratings", {}).items():
            if proj not in project_ratings_map:
                project_ratings_map[proj] = []
            project_ratings_map[proj].append(rating)
            
    project_summary = []
    for proj, ratings in project_ratings_map.items():
        project_summary.append({
            "project_name": proj,
            "average_rating": round(sum(ratings) / len(ratings), 2),
            "reviews_count": len(ratings)
        })
        
    user_promotions = [p for p in mock_db.promotions if p["user_id"] == user_id]
    
    detailed_feedbacks = []
    for fb in reviews:
        reviewer = next((p for p in mock_db.profiles if p["id"] == fb["reviewer_id"]), None)
        detailed_feedbacks.append({
            "id": fb["id"],
            "reviewer_name": reviewer["full_name"] if reviewer else "Anonymous Teammate",
            "reviewer_role": reviewer["role"] if reviewer else "Teammate",
            "type": fb["feedback_type"],
            "comments": fb["comments"],
            "ratings": {
                "quality": fb["rating_work_quality"],
                "collaboration": fb["rating_collaboration"],
                "leadership": fb["rating_leadership"]
            }
        })
        
    return {
        "year": year,
        "averages": {
            "work_quality": round(avg_quality, 2),
            "collaboration": round(avg_collab, 2),
            "leadership": round(avg_lead, 2)
        },
        "project_details": project_summary,
        "feedbacks": detailed_feedbacks,
        "promotions": user_promotions
    }

@router.post("/submit")
def submit_feedback(data: SubmitFeedbackRequest, user_id: str = Depends(get_current_user_id), db = Depends(get_db)):
    if db:
        new_fb = FeedbackDB(
            id=f"fb-{int(datetime.datetime.now().timestamp())}",
            user_id=user_id,
            reviewer_id=data.reviewer_id,
            feedback_type=data.feedback_type,
            year=data.year,
            rating_work_quality=data.rating_work_quality,
            rating_collaboration=data.rating_collaboration,
            rating_leadership=data.rating_leadership,
            comments=data.comments,
            project_ratings=data.project_ratings
        )
        db.add(new_fb)
        db.commit()
        return {"message": "Feedback submitted successfully"}
        
    # Fallback to mock DB
    new_fb = {
        "id": f"fb-{len(mock_db.feedbacks) + 1}",
        "user_id": user_id,
        "reviewer_id": data.reviewer_id,
        "feedback_type": data.feedback_type,
        "year": data.year,
        "rating_work_quality": data.rating_work_quality,
        "rating_collaboration": data.rating_collaboration,
        "rating_leadership": data.rating_leadership,
        "comments": data.comments,
        "project_ratings": data.project_ratings
    }
    mock_db.feedbacks.append(new_fb)
    return {"message": "Feedback submitted successfully", "feedback": new_fb}
