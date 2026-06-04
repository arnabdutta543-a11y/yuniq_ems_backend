from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import datetime
from database import get_db, FeedbackDB, ProfileDB, PromotionDB, PeerReviewAssignmentDB, SelfAppraisalDB, OkrDB
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

class PeerReviewSubmitRequest(BaseModel):
    assignment_id: int
    rating_work_quality: int
    rating_collaboration: int
    rating_leadership: int
    comments: str
    project_ratings: Dict[str, float]

class SelfAppraisalSubmitRequest(BaseModel):
    year: int
    q1_achievements: str
    q2_challenges: str
    linked_goals: List[int]
    supporting_docs: List[str]
    voice_summary_url: Optional[str] = None

def serialize_feedback(f: FeedbackDB, db, current_user_id: str) -> dict:
    reviewer_name = "Anonymous Peer"
    reviewer_role = "Teammate"
    
    # Anonymity rule: Only show reviewer name if type is manager
    if f.feedback_type == 'manager' and db:
        reviewer = db.query(ProfileDB).filter(ProfileDB.id == f.reviewer_id).first()
        if reviewer:
            reviewer_name = reviewer.full_name
            reviewer_role = reviewer.role
            
    return {
        "id": f.id,
        "reviewer_name": reviewer_name,
        "reviewer_role": reviewer_role,
        "type": f.feedback_type,
        "comments": f.comments,
        "ratings": {
            "quality": f.rating_work_quality,
            "collaboration": f.rating_collaboration,
            "leadership": f.rating_leadership
        }
    }

@router.get("/performance")
def get_performance_report(user_id: str = Depends(get_current_user_id), year: int = 2025, db = Depends(get_db)):
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
        
        detailed_feedbacks = [serialize_feedback(f, db, user_id) for f in reviews]
            
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
        
    return {
        "year": year,
        "averages": {"work_quality": 0, "collaboration": 0, "leadership": 0},
        "project_details": [],
        "feedbacks": [],
        "promotions": []
    }

@router.get("/performance/{emp_id}")
def get_employee_performance_report(emp_id: str, year: int = 2025, user_id: str = Depends(get_current_user_id), db = Depends(get_db)):
    """
    Exposes employee performance report to authorized supervisors (managers, HR leads).
    """
    if db:
        emp_profile = db.query(ProfileDB).filter(ProfileDB.id == emp_id).first()
        if not emp_profile:
            raise HTTPException(status_code=404, detail="Employee profile not found")
            
        curr_user = db.query(ProfileDB).filter(ProfileDB.id == user_id).first()
        if not curr_user:
            raise HTTPException(status_code=403, detail="User not found")
            
        is_authorized = (
            user_id == emp_id or
            curr_user.role in ["HR Manager", "Director"] or
            emp_profile.manager_id == user_id
        )
        if not is_authorized:
            raise HTTPException(status_code=403, detail="You do not have permission to view this employee's performance report")
            
        reviews = db.query(FeedbackDB).filter(FeedbackDB.user_id == emp_id, FeedbackDB.year == year).all()
        avg_quality = sum(f.rating_work_quality for f in reviews) / len(reviews) if reviews else 0.0
        avg_collab = sum(f.rating_collaboration for f in reviews) / len(reviews) if reviews else 0.0
        avg_lead = sum(f.rating_leadership for f in reviews) / len(reviews) if reviews else 0.0
        
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
            
        promotions_records = db.query(PromotionDB).filter(PromotionDB.user_id == emp_id).all()
        promotions_list = [{
            "id": p.id,
            "old_role": p.old_role,
            "new_role": p.new_role,
            "date": p.date.isoformat(),
            "details": p.details
        } for p in promotions_records]
        
        detailed_feedbacks = [serialize_feedback(f, db, user_id) for f in reviews]
        
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
    return {}

@router.get("/peer-assignments")
def get_peer_assignments(user_id: str = Depends(get_current_user_id), db = Depends(get_db)):
    if db:
        assignments = db.query(PeerReviewAssignmentDB).filter(
            PeerReviewAssignmentDB.reviewer_id == user_id
        ).all()
        
        results = []
        for a in assignments:
            emp = db.query(ProfileDB).filter(ProfileDB.id == a.employee_id).first()
            results.append({
                "id": a.id,
                "employee_id": a.employee_id,
                "employee_name": emp.full_name if emp else "Unknown Employee",
                "employee_role": emp.role if emp else "Teammate",
                "year": a.year,
                "status": a.status
            })
        return results
    return []

@router.post("/submit-peer-review")
def submit_peer_review(data: PeerReviewSubmitRequest, user_id: str = Depends(get_current_user_id), db = Depends(get_db)):
    if db:
        # Verify assignment
        assignment = db.query(PeerReviewAssignmentDB).filter(
            PeerReviewAssignmentDB.id == data.assignment_id,
            PeerReviewAssignmentDB.reviewer_id == user_id
        ).first()
        
        if not assignment:
            raise HTTPException(status_code=404, detail="Peer review assignment not found")
        if assignment.status == "Submitted":
            raise HTTPException(status_code=400, detail="Peer review has already been submitted")
            
        new_fb = FeedbackDB(
            user_id=assignment.employee_id,
            reviewer_id=user_id,
            feedback_type="peer",
            year=assignment.year,
            rating_work_quality=data.rating_work_quality,
            rating_collaboration=data.rating_collaboration,
            rating_leadership=data.rating_leadership,
            comments=data.comments,
            project_ratings=data.project_ratings
        )
        db.add(new_fb)
        assignment.status = "Submitted"
        db.commit()
        return {"message": "Peer review submitted successfully"}
    return {"message": "Submitted"}

@router.get("/self-appraisal")
def get_self_appraisal(year: int = 2026, user_id: str = Depends(get_current_user_id), db = Depends(get_db)):
    if db:
        appraisal = db.query(SelfAppraisalDB).filter(
            SelfAppraisalDB.employee_id == user_id,
            SelfAppraisalDB.year == year
        ).first()
        
        if not appraisal:
            return None
            
        # Get goals detail
        goals_data = []
        if appraisal.linked_goals:
            goals = db.query(OkrDB).filter(OkrDB.id.in_(appraisal.linked_goals)).all()
            for g in goals:
                goals_data.append({
                    "id": g.id,
                    "objective": g.objective,
                    "progress": g.progress
                })
                
        return {
            "id": appraisal.id,
            "year": appraisal.year,
            "q1_achievements": appraisal.q1_achievements,
            "q2_challenges": appraisal.q2_challenges,
            "linked_goals": appraisal.linked_goals,
            "linked_goals_detail": goals_data,
            "supporting_docs": appraisal.supporting_docs,
            "voice_summary_url": appraisal.voice_summary_url,
            "submitted_at": appraisal.submitted_at.isoformat()
        }
    return None

@router.post("/self-appraisal")
def submit_self_appraisal(data: SelfAppraisalSubmitRequest, user_id: str = Depends(get_current_user_id), db = Depends(get_db)):
    if db:
        # Check if already exists
        appraisal = db.query(SelfAppraisalDB).filter(
            SelfAppraisalDB.employee_id == user_id,
            SelfAppraisalDB.year == data.year
        ).first()
        
        if appraisal:
            appraisal.q1_achievements = data.q1_achievements
            appraisal.q2_challenges = data.q2_challenges
            appraisal.linked_goals = data.linked_goals
            appraisal.supporting_docs = data.supporting_docs
            if data.voice_summary_url:
                appraisal.voice_summary_url = data.voice_summary_url
            appraisal.submitted_at = datetime.datetime.now()
        else:
            appraisal = SelfAppraisalDB(
                employee_id=user_id,
                year=data.year,
                q1_achievements=data.q1_achievements,
                q2_challenges=data.q2_challenges,
                linked_goals=data.linked_goals,
                supporting_docs=data.supporting_docs,
                voice_summary_url=data.voice_summary_url,
                submitted_at=datetime.datetime.now()
            )
            db.add(appraisal)
            
        db.commit()
        return {"message": "Self-appraisal submitted successfully"}
    return {"message": "Self-appraisal submitted"}
