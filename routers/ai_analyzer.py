from fastapi import APIRouter, Depends, HTTPException
from database import mock_db, get_db, FeedbackDB, TrainingDB
from routers.auth import get_current_user_id
from typing import List, Dict, Any

router = APIRouter(prefix="/ai-analyzer", tags=["ai-analyzer"])

@router.get("/summary")
def get_ai_analysis_summary(user_id: str = Depends(get_current_user_id), db = Depends(get_db)):
    feedbacks_list = []
    completed_trainings = 0
    
    if db:
        feedbacks_list = db.query(FeedbackDB).filter(FeedbackDB.user_id == user_id).all()
        completed_trainings = db.query(TrainingDB).filter(
            TrainingDB.user_id == user_id, 
            TrainingDB.status == "Completed"
        ).count()
    else:
        # Fallback to mock DB
        feedbacks_list = [f for f in mock_db.feedbacks if f["user_id"] == user_id]
        completed_trainings = len([t for t in mock_db.trainings if t["user_id"] == user_id and t["status"] == "Completed"])
        
    if not feedbacks_list:
        return {
            "promotion_readiness": 50.0,
            "sentiment": "Neutral",
            "strengths": ["Basic Task Execution"],
            "development_areas": ["Awaiting feedback reviews for full analysis"],
            "career_coach_recommendation": "Submit peer and manager feedback reviews to activate career coaching algorithms."
        }
        
    # Rule-Based NLP and Metric calculations
    total_quality = 0.0
    total_collab = 0.0
    total_lead = 0.0
    all_comments = []
    
    for f in feedbacks_list:
        if db:
            total_quality += f.rating_work_quality
            total_collab += f.rating_collaboration
            total_lead += f.rating_leadership
            if f.comments:
                all_comments.append(f.comments.lower())
        else:
            total_quality += f["rating_work_quality"]
            total_collab += f["rating_collaboration"]
            total_lead += f["rating_leadership"]
            if f.get("comments"):
                all_comments.append(f["comments"].lower())
                
    count = len(feedbacks_list)
    avg_quality = total_quality / count
    avg_collab = total_collab / count
    avg_lead = total_lead / count
    overall_avg = (avg_quality + avg_collab + avg_lead) / 3.0
    
    # Calculate Promotion Readiness Score (Base: overall rating / 5 * 85%, Add-ons: completed courses up to 15%)
    base_score = (overall_avg / 5.0) * 85.0
    course_bonus = min(15.0, completed_trainings * 5.0)
    promotion_readiness = min(100.0, round(base_score + course_bonus, 1))
    
    # Sentiment calculation
    if overall_avg >= 4.5:
        sentiment = "Highly Positive"
    elif overall_avg >= 4.0:
        sentiment = "Positive"
    elif overall_avg >= 3.0:
        sentiment = "Neutral"
    else:
        sentiment = "Constructive"
        
    # Rule-Based Strengths extraction
    strengths = []
    text_blob = " ".join(all_comments)
    
    if avg_quality >= 4.0 or "quality" in text_blob or "delivers" in text_blob:
        strengths.append("High Quality Deliverables & Work Ethics")
    if avg_collab >= 4.0 or "helpful" in text_blob or "teammate" in text_blob:
        strengths.append("Excellent Collaborative Synergy & Teamwork")
    if avg_lead >= 4.0 or "ownership" in text_blob or "leads" in text_blob:
        strengths.append("Proactive Technical Leadership & Ownership")
    if "architecture" in text_blob or "designs" in text_blob:
        strengths.append("Robust System Architecture & Design Thinking")
    if "decision" in text_blob or "rules" in text_blob:
        strengths.append("Expertise in Business Logic Modeling & Decision Orchestration")
        
    if not strengths:
        strengths.append("Solid Core Software Development Skills")
        
    # Rule-Based Development areas extraction
    development_areas = []
    if avg_lead < 4.2:
        development_areas.append("Take higher initiative in leading cross-functional meetings")
    if avg_collab < 4.2:
        development_areas.append("Improve technical communication channels in hybrid setups")
    if completed_trainings < 2:
        development_areas.append("Upskill in recommended Vercel & Supabase Cloud Architectures")
    if "improve" in text_blob or "could focus" in text_blob or "speed" in text_blob:
        development_areas.append("Optimize task velocity and delegation patterns")
        
    if not development_areas:
        development_areas.append("Continue maintaining the high standard of performance; focus on mentoring junior peers.")
        
    # Career Coach recommendation
    if promotion_readiness >= 90.0:
        coach_rec = "Strong candidate for immediate promotion to Lead Consultant. Recommended action: Submit the internal resume to HR for review."
    elif promotion_readiness >= 75.0:
        coach_rec = "Solid performer. To secure promotion in the next cycle, enroll in 'Next.js Advanced Routing' and focus on taking larger design ownership."
    else:
        coach_rec = "Focus on closing core learning milestones. Seek regular feedback loops to improve collaboration metrics."
        
    return {
        "promotion_readiness": promotion_readiness,
        "sentiment": sentiment,
        "strengths": strengths,
        "development_areas": development_areas,
        "career_coach_recommendation": coach_rec
    }
