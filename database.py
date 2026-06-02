import datetime
from typing import Dict, List, Any, Optional
import json
import os
from sqlalchemy import create_engine, Column, String, Integer, Float, Date, Boolean, JSON, ForeignKey, Numeric, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from config import settings

Base = declarative_base()

# SQLAlchemy Models

class ProfileDB(Base):
    __tablename__ = 'profiles'
    id = Column(String(50), primary_key=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    role = Column(String(100), nullable=False)
    department = Column(String(100), nullable=False)
    manager_id = Column(String(50), ForeignKey('profiles.id', ondelete='SET NULL'), nullable=True)
    avatar_url = Column(Text, nullable=True)

class AttendanceLogDB(Base):
    __tablename__ = 'attendance_logs'
    id = Column(String(50), primary_key=True)
    user_id = Column(String(50), ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False)
    date = Column(Date, nullable=False)
    punch_in_at = Column(String(50), nullable=False)
    punch_out_at = Column(String(50), nullable=True)
    total_hours = Column(Float, default=0.0)
    activity_log = Column(JSON, default=list) # List of dicts [{"time":..., "action":...}]

class TimesheetDB(Base):
    __tablename__ = 'timesheets'
    id = Column(String(50), primary_key=True)
    user_id = Column(String(50), ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False)
    week_start = Column(Date, nullable=False)
    status = Column(String(20), default='Draft')
    entries = Column(JSON, nullable=False) # List of daily entries

class LeaveDB(Base):
    __tablename__ = 'leaves'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False)
    leave_type = Column(String(50), nullable=False)
    from_date = Column(Date, nullable=False)
    to_date = Column(Date, nullable=False)
    num_days = Column(Float, nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(String(20), default='Pending')
    applied_date = Column(Date, nullable=False)
    recalled = Column(Boolean, default=False)

class HolidayDB(Base):
    __tablename__ = 'holidays'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    date = Column(Date, nullable=False)
    day = Column(String(10), nullable=False)

class PolicyDB(Base):
    __tablename__ = 'policies'
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(150), nullable=False)
    category = Column(String(50), nullable=False)
    url = Column(Text, nullable=False)
    published_at = Column(Date, nullable=False)

class FeedbackDB(Base):
    __tablename__ = 'feedbacks'
    id = Column(String(50), primary_key=True)
    user_id = Column(String(50), ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False)
    reviewer_id = Column(String(50), ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False)
    feedback_type = Column(String(20), nullable=False) # peer/manager
    year = Column(Integer, nullable=False)
    rating_work_quality = Column(Integer, nullable=False)
    rating_collaboration = Column(Integer, nullable=False)
    rating_leadership = Column(Integer, nullable=False)
    comments = Column(Text, nullable=True)
    project_ratings = Column(JSON, default=dict)

class PromotionDB(Base):
    __tablename__ = 'promotions'
    id = Column(String(50), primary_key=True)
    user_id = Column(String(50), ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False)
    old_role = Column(String(100), nullable=False)
    new_role = Column(String(100), nullable=False)
    date = Column(Date, nullable=False)
    details = Column(Text, nullable=True)

class TravelRequestDB(Base):
    __tablename__ = 'travel_requests'
    id = Column(String(50), primary_key=True)
    user_id = Column(String(50), ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False)
    destination = Column(String(100), nullable=False)
    departure_date = Column(Date, nullable=False)
    return_date = Column(Date, nullable=False)
    status = Column(String(30), default='Pending Approval')
    selected_flight = Column(JSON, nullable=True)
    selected_hotel = Column(JSON, nullable=True)

class NotificationDB(Base):
    __tablename__ = 'notifications'
    id = Column(String(50), primary_key=True)
    user_id = Column(String(50), ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False)
    title = Column(String(150), nullable=False)
    message = Column(Text, nullable=False)
    read = Column(Boolean, default=False)
    created_at = Column(String(50), nullable=False)

class SkillDB(Base):
    __tablename__ = 'skills'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False)
    skill_name = Column(String(100), nullable=False)
    proficiency = Column(Integer, nullable=False)
    category = Column(String(50), nullable=False)

class CertificationDB(Base):
    __tablename__ = 'certifications'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False)
    name = Column(String(150), nullable=False)
    authority = Column(String(100), nullable=False)
    issued_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=True)
    url = Column(Text, nullable=True)

class OkrDB(Base):
    __tablename__ = 'okrs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False)
    type = Column(String(20), nullable=False)
    objective = Column(Text, nullable=False)
    key_results = Column(JSON, nullable=False)
    progress = Column(Float, default=0.0)
    year = Column(Integer, nullable=False)
    quarter = Column(Integer, nullable=False)

class RecognitionDB(Base):
    __tablename__ = 'recognitions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False)
    award_type = Column(String(50), nullable=False)
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=False)
    given_by = Column(String(100), nullable=False)
    date = Column(Date, nullable=False)

class TrainingDB(Base):
    __tablename__ = 'trainings'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False)
    course_name = Column(String(150), nullable=False)
    provider = Column(String(100), nullable=False)
    status = Column(String(30), nullable=False)
    progress = Column(Float, default=0.0)
    recommended_by_ai = Column(Boolean, default=False)

class PayrollDB(Base):
    __tablename__ = 'payrolls'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), ForeignKey('profiles.id', ondelete='CASCADE'), unique=True, nullable=False)
    salary_base = Column(Float, nullable=False)
    salary_allowance = Column(Float, nullable=False)
    tax_deduction = Column(Float, nullable=False)
    increment_history = Column(JSON, default=list)
    payslips = Column(JSON, default=list)

class ClaimDB(Base):
    __tablename__ = 'claims'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    date = Column(Date, nullable=False)
    status = Column(String(20), default='Pending')

class AssetDB(Base):
    __tablename__ = 'assets'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False)
    asset_name = Column(String(150), nullable=False)
    serial_number = Column(String(100), nullable=False)
    assigned_date = Column(Date, nullable=False)
    status = Column(String(30), default='Assigned')

class AnnouncementDB(Base):
    __tablename__ = 'announcements'
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(150), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)
    created_at = Column(Date, nullable=False)

class KnowledgeBaseDB(Base):
    __tablename__ = 'knowledge_base'
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(150), nullable=False)
    category = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    url = Column(Text, nullable=False)

# Thread-safe in-memory database for mock mode fallback
class MockDatabase:
    def __init__(self):
        self.profiles = [
            {"id": "user-saket", "full_name": "Mr. SAKET RANJAN", "email": "saket.ranjan@yuniq.com", "role": "Director", "department": "Management", "manager_id": None, "avatar_url": ""},
            {"id": "user-abhyudaya", "full_name": "Mr. ABHYUDAYA SINGH", "email": "abhyudaya.singh@yuniq.com", "role": "Consultant", "department": "DECISIONS", "manager_id": "user-saket", "avatar_url": ""},
            {"id": "user-ajay", "full_name": "AJAY RAGHUL", "email": "ajay.raghul@yuniq.com", "role": "Senior Engineer", "department": "PEGA", "manager_id": "user-saket", "avatar_url": ""},
            {"id": "user-anjana", "full_name": "ANJANA SINGH", "email": "anjana.singh@yuniq.com", "role": "Lead Architect", "department": "DECISIONS", "manager_id": "user-saket", "avatar_url": ""},
            {"id": "user-annesha", "full_name": "ANNESHA DUTTA", "email": "annesha.dutta@yuniq.com", "role": "HR Manager", "department": "HR", "manager_id": "user-saket", "avatar_url": ""},
            {"id": "user-arnab", "full_name": "ARNAB DUTTA", "email": "arnab.dutta@yuniq.com", "role": "Associate Consultant", "department": "DECISIONS", "manager_id": "user-saket", "avatar_url": ""},
            {"id": "user-debarati", "full_name": "DEBARATI PATRA", "email": "debarati.patra@yuniq.com", "role": "Senior Consultant", "department": "DECISIONS", "manager_id": "user-saket", "avatar_url": ""},
            {"id": "user-debolina", "full_name": "DEBOLINA BOSE", "email": "debolina.bose@yuniq.com", "role": "Senior Consultant", "department": "DECISIONS", "manager_id": "user-saket", "avatar_url": ""},
            {"id": "user-dhivagar", "full_name": "DHIVAGAR K", "email": "dhivagar.k@yuniq.com", "role": "Senior Engineer", "department": "DECISIONS", "manager_id": "user-saket", "avatar_url": ""},
            {"id": "user-karthick", "full_name": "KARTHICK RAJAN", "email": "karthick.rajan@yuniq.com", "role": "Senior Consultant", "department": "DECISIONS", "manager_id": "user-saket", "avatar_url": ""},
        ]
        self.attendance_logs = [
            {"id": "att-1", "user_id": "user-debarati", "date": "2026-06-01", "punch_in_at": "2026-06-01T09:00:00Z", "punch_out_at": "2026-06-01T18:00:00Z", "total_hours": 9.0, "activity_log": [{"time": "2026-06-01T09:00:00Z", "action": "Punch-In"}, {"time": "2026-06-01T18:00:00Z", "action": "Punch-Out"}]}
        ]
        self.active_punches: Dict[str, str] = {}
        self.timesheets = [
            {
                "id": "ts-1",
                "user_id": "user-debarati",
                "week_start": "2026-06-01",
                "status": "Submitted",
                "entries": [
                    {"date": "2026-06-01", "project": "Decisions", "hours": 8.0, "description": "Worked on decision engines and rule orchestration backend."},
                    {"date": "2026-06-02", "project": "Decisions", "hours": 8.0, "description": "Reviewed UI-UX mockup styling integrations."},
                    {"date": "2026-06-03", "project": "Decisions", "hours": 8.0, "description": "Backend architecture alignment and dockerization setup."},
                    {"date": "2026-06-04", "project": "Decisions", "hours": 8.0, "description": "Database migrations and performance analytics charts setup."},
                    {"date": "2026-06-05", "project": "Decisions", "hours": 8.0, "description": "Client sync and travel management portal search integration."},
                    {"date": "2026-06-06", "project": "None", "hours": 0.0, "description": ""},
                    {"date": "2026-06-07", "project": "None", "hours": 0.0, "description": ""}
                ]
            }
        ]
        self.leaves = [
            {"id": 1, "user_id": "user-debarati", "leave_type": "Other", "from_date": "2026-05-25", "to_date": "2026-05-25", "num_days": 1.0, "reason": "I had doctor's appointment in the morning.", "status": "Approved", "applied_date": "2026-05-27", "recalled": False},
            {"id": 2, "user_id": "user-debarati", "leave_type": "Sick Leave", "from_date": "2026-11-05", "to_date": "2026-11-05", "num_days": 1.0, "reason": "I am not feeling well.", "status": "Approved", "applied_date": "2026-11-05", "recalled": False},
            {"id": 3, "user_id": "user-debarati", "leave_type": "Other", "from_date": "2026-07-24", "to_date": "2026-07-24", "num_days": 1.0, "reason": "I will be traveling out of town.", "status": "Approved", "applied_date": "2026-07-24", "recalled": False},
            {"id": 4, "user_id": "user-debarati", "leave_type": "Other", "from_date": "2026-04-21", "to_date": "2026-04-21", "num_days": 0.5, "reason": "I live with my aunt and need to help her.", "status": "Approved", "applied_date": "2026-04-21", "recalled": False},
            {"id": 5, "user_id": "user-debarati", "leave_type": "Other", "from_date": "2026-03-30", "to_date": "2026-03-31", "num_days": 2.0, "reason": "My aunt who lives with me is sick.", "status": "Approved", "applied_date": "2026-03-31", "recalled": False},
            {"id": 6, "user_id": "user-debarati", "leave_type": "Other", "from_date": "2026-03-20", "to_date": "2026-03-20", "num_days": 0.5, "reason": "I got a call from bank regarding home loan verification.", "status": "Approved", "applied_date": "2026-03-19", "recalled": False},
            {"id": 7, "user_id": "user-debarati", "leave_type": "Other", "from_date": "2026-03-18", "to_date": "2026-03-18", "num_days": 1.0, "reason": "I have a doctor's appointment today.", "status": "Approved", "applied_date": "2026-03-17", "recalled": False},
            {"id": 8, "user_id": "user-debarati", "leave_type": "Other", "from_date": "2026-03-17", "to_date": "2026-03-17", "num_days": 1.0, "reason": "My aunt has an eye checkup.", "status": "Recalled", "applied_date": "2026-03-16", "recalled": True},
            {"id": 9, "user_id": "user-debarati", "leave_type": "Other", "from_date": "2026-03-03", "to_date": "2026-03-03", "num_days": 1.0, "reason": "Due to Holi celebration, traveling home.", "status": "Approved", "applied_date": "2026-02-03", "recalled": False}
        ]
        self.holidays = [
            {"id": 1, "name": "Independence Day", "date": "2026-08-15", "day": "Sat"},
            {"id": 2, "name": "Rakshabandhan", "date": "2026-08-28", "day": "Fri"},
            {"id": 3, "name": "Ganesh Chaturthi", "date": "2026-09-14", "day": "Mon"},
            {"id": 4, "name": "Gandhi Jayanthi", "date": "2026-10-02", "day": "Fri"},
            {"id": 5, "name": "Mahanavmi", "date": "2026-10-20", "day": "Tue"},
            {"id": 6, "name": "Christmas", "date": "2026-12-25", "day": "Fri"},
            {"id": 7, "name": "New Year's Day", "date": "2026-01-01", "day": "Thu"},
            {"id": 8, "name": "Republic Day", "date": "2026-01-26", "day": "Mon"}
        ]
        self.policies = [
            {"id": 1, "title": "Employee Conduct & Integrity Guidelines", "category": "HR Policy", "url": "/policies/conduct.pdf", "published_at": "2025-01-10"},
            {"id": 2, "title": "Travel & Expense Reimbursement Policy v3.0", "category": "Finance", "url": "/policies/travel_policy.pdf", "published_at": "2025-08-15"},
            {"id": 3, "title": "IT Asset Allocation & Remote Work Policy", "category": "IT", "url": "/policies/it_asset.pdf", "published_at": "2026-02-01"},
            {"id": 4, "title": "Leave Policy Guidelines (2026)", "category": "HR Policy", "url": "/policies/leave_policy.pdf", "published_at": "2026-01-01"}
        ]
        self.feedbacks = [
            {"id": "fb-1", "user_id": "user-debarati", "reviewer_id": "user-saket", "feedback_type": "manager", "year": 2025, "rating_work_quality": 5, "rating_collaboration": 4, "rating_leadership": 4, "comments": "Debarati consistently delivers high quality solutions. She has demonstrated solid ownership of the decisions modules and provides valuable guidance to junior peers.", "project_ratings": {"Decisions": 4.8, "Client X": 4.5}},
            {"id": "fb-2", "user_id": "user-debarati", "reviewer_id": "user-abhyudaya", "feedback_type": "peer", "year": 2025, "rating_work_quality": 4, "rating_collaboration": 5, "rating_leadership": 4, "comments": "Great teammate to work with. Always helpful when resolving technical roadblocks in project integrations.", "project_ratings": {"Decisions": 4.5}},
            {"id": "fb-3", "user_id": "user-debarati", "reviewer_id": "user-anjana", "feedback_type": "peer", "year": 2025, "rating_work_quality": 5, "rating_collaboration": 4, "rating_leadership": 5, "comments": "Her architectural designs are highly sustainable. Highly professional and leads core initiatives effectively.", "project_ratings": {"Decisions": 5.0}}
        ]
        self.promotions = [
            {"id": "promo-1", "user_id": "user-debarati", "old_role": "Software Engineer", "new_role": "Senior Engineer", "date": "2023-04-01", "details": "Promoted for exceptional contributions in the client onboarding workflows."},
            {"id": "promo-2", "user_id": "user-debarati", "old_role": "Senior Engineer", "new_role": "Senior Consultant", "date": "2025-04-01", "details": "Promoted for leadership in platform revamps and decision system integration."}
        ]
        self.travel_requests = [
            {
                "id": "travel-1",
                "user_id": "user-debarati",
                "destination": "San Francisco, USA",
                "departure_date": "2026-07-10",
                "return_date": "2026-07-20",
                "status": "Approved",
                "selected_flight": {"flight_num": "UA 890", "carrier": "United Airlines", "price": 1250.0, "departure": "BOM 09:30 AM", "arrival": "SFO 01:15 PM"},
                "selected_hotel": {"name": "Hilton Union Square", "price_per_night": 220.0, "rating": 4.2}
            }
        ]
        self.notifications = [
            {"id": "notif-1", "user_id": "user-debarati", "title": "Leave Approved", "message": "Your leave request for 25-05-2026 has been approved.", "read": False, "created_at": "2026-05-27T10:00:00Z"},
            {"id": "notif-2", "user_id": "user-debarati", "title": "Timesheet Submitted", "message": "Weekly timesheet (Jun 1 - Jun 7) submitted successfully.", "read": True, "created_at": "2026-06-02T11:00:00Z"},
            {"id": "notif-3", "user_id": "user-debarati", "title": "Yearly Performance Available", "message": "Your performance report for year 2025 is now active.", "read": False, "created_at": "2026-06-01T09:00:00Z"}
        ]
        
        # New Enterprise Extension mock tables (in-memory)
        self.skills = [
            {"id": 1, "user_id": "user-debarati", "skill_name": "Next.js (React)", "proficiency": 5, "category": "Technical"},
            {"id": 2, "user_id": "user-debarati", "skill_name": "FastAPI (Python)", "proficiency": 4, "category": "Technical"},
            {"id": 3, "user_id": "user-debarati", "skill_name": "TypeScript", "proficiency": 4, "category": "Technical"},
            {"id": 4, "user_id": "user-debarati", "skill_name": "PostgreSQL", "proficiency": 4, "category": "Technical"},
            {"id": 5, "user_id": "user-debarati", "skill_name": "Decision Modeling", "proficiency": 5, "category": "Technical"},
            {"id": 6, "user_id": "user-debarati", "skill_name": "Strategic Planning", "proficiency": 4, "category": "Soft Skills"},
            {"id": 7, "user_id": "user-debarati", "skill_name": "Technical Leadership", "proficiency": 4, "category": "Soft Skills"},
        ]
        
        self.certifications = [
            {"id": 1, "user_id": "user-debarati", "name": "AWS Certified Solutions Architect", "authority": "Amazon Web Services", "issued_date": "2024-05-10", "expiry_date": "2027-05-10", "url": "#"},
            {"id": 2, "user_id": "user-debarati", "name": "Certified ScrumMaster (CSM)", "authority": "Scrum Alliance", "issued_date": "2025-01-15", "expiry_date": "2027-01-15", "url": "#"}
        ]
        
        self.okrs = [
            {"id": 1, "user_id": "user-debarati", "type": "Personal", "objective": "Optimize Compilation Pipeline", "key_results": [{"kr": "Reduce Next.js Turbopack build time by 30%", "progress": 85}, {"kr": "Achieve 98% type coverage in TypeScript files", "progress": 100}], "progress": 92.5, "year": 2026, "quarter": 2},
            {"id": 2, "user_id": "user-debarati", "type": "Team", "objective": "Revamp Employee Portal UX", "key_results": [{"kr": "Deploy CSS module layout variables", "progress": 100}, {"kr": "Integrate Google travel bookings", "progress": 90}], "progress": 95.0, "year": 2026, "quarter": 2},
            {"id": 3, "user_id": "user-debarati", "type": "Organization", "objective": "Achieve SOC2 Security Compliance", "key_results": [{"kr": "Audits completed for key database instances", "progress": 60}], "progress": 60.0, "year": 2026, "quarter": 2}
        ]
        
        self.recognitions = [
            {"id": 1, "user_id": "user-debarati", "award_type": "Spot Award", "title": "Portal Revamp Champion", "description": "Recognized by management for outstanding execution on the employee portal design.", "given_by": "Mr. SAKET RANJAN", "date": "2026-06-01"},
            {"id": 2, "user_id": "user-debarati", "award_type": "Employee of the Month", "title": "Excellence in Action", "description": "Demonstrated consistent quality in database optimizations.", "given_by": "ANNESHA DUTTA", "date": "2026-05-01"}
        ]
        
        self.trainings = [
            {"id": 1, "user_id": "user-debarati", "course_name": "Next.js Advanced Routing & App Router Architectures", "provider": "Vercel Academy", "status": "In Progress", "progress": 65.0, "recommended_by_ai": True},
            {"id": 2, "user_id": "user-debarati", "course_name": "High-Performance Python Architectures (FastAPI)", "provider": "FastAPI Certified", "status": "Completed", "progress": 100.0, "recommended_by_ai": False},
            {"id": 3, "user_id": "user-debarati", "course_name": "PostgreSQL Performance Optimization & Indexing", "provider": "Supabase University", "status": "Recommended", "progress": 0.0, "recommended_by_ai": True}
        ]
        
        self.payroll = {
            "user_id": "user-debarati",
            "salary_base": 12500.00,
            "salary_allowance": 4200.00,
            "tax_deduction": 1850.00,
            "increment_history": [
                {"id": 1, "date": "2024-04-01", "old_salary": 11000.00, "new_salary": 13500.00, "percentage": 22.7},
                {"id": 2, "date": "2025-04-01", "old_salary": 13500.00, "new_salary": 16700.00, "percentage": 23.7}
            ],
            "payslips": [
                {"month": "May 2026", "net": 14850.00, "download_url": "#"},
                {"month": "April 2026", "net": 14850.00, "download_url": "#"},
                {"month": "March 2026", "net": 14850.00, "download_url": "#"}
            ]
        }
        
        self.assets = [
            {"id": 1, "user_id": "user-debarati", "asset_name": "MacBook Pro M3 Max (16-inch, Space Black)", "serial_number": "C02G2X89Q05D", "assigned_date": "2025-10-15", "status": "Assigned"},
            {"id": 2, "user_id": "user-debarati", "asset_name": "Dell UltraSharp 27-inch 4K Monitor", "serial_number": "CN-0F8912-1082", "assigned_date": "2025-10-15", "status": "Assigned"}
        ]
        
        self.announcements = [
            {"id": 1, "title": "Corporate Townhall Meeting Scheduled", "content": "Join our quarterly updates meeting with the leadership team tomorrow at 4:00 PM in Conference Room A or virtually.", "category": "Company", "created_at": "2026-06-02"},
            {"id": 2, "title": "Decisions Integration Milestone Achieved", "content": "Congratulations to the Decisions integration team for deploying the automated workflow systems ahead of schedule!", "category": "Department", "created_at": "2026-06-01"}
        ]
        
        self.knowledge_base = [
            {"id": 1, "title": "Git Branching & Release SOP", "category": "SOP", "content": "Overview of branching directories, pull requests templates, and merge checks.", "url": "#"},
            {"id": 2, "title": "FastAPI Router Setup Guide", "category": "SOP", "content": "Standards for structuring router files, dependency injection, and schemas.", "url": "#"},
            {"id": 3, "title": "Next.js Tailwind CSS Modules Template", "category": "Template", "content": "Base configuration file for styling layout modules.", "url": "#"}
        ]
        
        self.claims = [
            {"id": 1, "user_id": "user-debarati", "amount": 120.00, "category": "Travel", "description": "Taxi fare to airport", "date": "2026-06-01", "status": "Approved"},
            {"id": 2, "user_id": "user-debarati", "amount": 45.00, "category": "Meals", "description": "Business lunch with client", "date": "2026-06-02", "status": "Pending"}
        ]

mock_db = MockDatabase()

# Setup PostgreSQL Database Session
engine = None
SessionLocal = None
is_db_connected = False

if not settings.is_mock_mode and settings.DATABASE_URL:
    try:
        # Create Engine and SessionMaker
        # Note: the connection URL password was already percent-encoded in config.py
        engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # Test connection
        with engine.connect() as conn:
            is_db_connected = True
            print("Successfully connected to Supabase PostgreSQL Database!")
    except Exception as e:
        print(f"PostgreSQL connection failed: {e}. Falling back to Mock Database.")
        is_db_connected = False

def get_db():
    """
    FastAPI dependency yielding database sessions.
    If database is not connected, returns None.
    """
    if not is_db_connected or not SessionLocal:
        yield None
        return
        
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Startup Database Schema Initializer & Seeding
def init_db():
    """
    Executes Base.metadata.create_all to ensure all tables exist in Supabase.
    Pre-populates tables with initial mock entries if they are empty.
    """
    if not is_db_connected or not engine:
        print("Database not connected. Skipping DDL schema creation.")
        return
        
    try:
        # 1. Create all tables if they don't exist
        Base.metadata.create_all(bind=engine)
        print("SQLAlchemy Base schema initialized in database.")
        
        # 2. Seed tables if they are empty
        db = SessionLocal()
        
        # Seed Profiles
        if db.query(ProfileDB).count() == 0:
            print("Seeding profiles table...")
            for p in mock_db.profiles:
                db.add(ProfileDB(
                    id=p["id"],
                    full_name=p["full_name"],
                    email=p["email"],
                    role=p["role"],
                    department=p["department"],
                    manager_id=p["manager_id"]
                ))
            db.commit()
            
        # Seed Holidays
        if db.query(HolidayDB).count() == 0:
            print("Seeding holidays table...")
            for h in mock_db.holidays:
                db.add(HolidayDB(
                    name=h["name"],
                    date=datetime.date.fromisoformat(h["date"]),
                    day=h["day"]
                ))
            db.commit()
            
        # Seed Policies
        if db.query(PolicyDB).count() == 0:
            print("Seeding policies table...")
            for po in mock_db.policies:
                db.add(PolicyDB(
                    title=po["title"],
                    category=po["category"],
                    url=po["url"],
                    published_at=datetime.date.fromisoformat(po["published_at"])
                ))
            db.commit()

        # Seed Feedbacks
        if db.query(FeedbackDB).count() == 0:
            print("Seeding feedbacks table...")
            for f in mock_db.feedbacks:
                db.add(FeedbackDB(
                    id=f["id"],
                    user_id=f["user_id"],
                    reviewer_id=f["reviewer_id"],
                    feedback_type=f["feedback_type"],
                    year=f["year"],
                    rating_work_quality=f["rating_work_quality"],
                    rating_collaboration=f["rating_collaboration"],
                    rating_leadership=f["rating_leadership"],
                    comments=f["comments"],
                    project_ratings=f["project_ratings"]
                ))
            db.commit()

        # Seed Promotions
        if db.query(PromotionDB).count() == 0:
            print("Seeding promotions table...")
            for pr in mock_db.promotions:
                db.add(PromotionDB(
                    id=pr["id"],
                    user_id=pr["user_id"],
                    old_role=pr["old_role"],
                    new_role=pr["new_role"],
                    date=datetime.date.fromisoformat(pr["date"]),
                    details=pr["details"]
                ))
            db.commit()

        # Seed Timesheets
        if db.query(TimesheetDB).count() == 0:
            print("Seeding timesheets table...")
            for ts in mock_db.timesheets:
                db.add(TimesheetDB(
                    id=ts["id"],
                    user_id=ts["user_id"],
                    week_start=datetime.date.fromisoformat(ts["week_start"]),
                    status=ts["status"],
                    entries=ts["entries"]
                ))
            db.commit()

        # Seed Leaves
        if db.query(LeaveDB).count() == 0:
            print("Seeding leaves table...")
            for l in mock_db.leaves:
                db.add(LeaveDB(
                    user_id=l["user_id"],
                    leave_type=l["leave_type"],
                    from_date=datetime.date.fromisoformat(l["from_date"]),
                    to_date=datetime.date.fromisoformat(l["to_date"]),
                    num_days=l["num_days"],
                    reason=l["reason"],
                    status=l["status"],
                    applied_date=datetime.date.fromisoformat(l["applied_date"]),
                    recalled=l["recalled"]
                ))
            db.commit()

        # Seed Notifications
        if db.query(NotificationDB).count() == 0:
            print("Seeding notifications table...")
            for n in mock_db.notifications:
                db.add(NotificationDB(
                    id=n["id"],
                    user_id=n["user_id"],
                    title=n["title"],
                    message=n["message"],
                    read=n["read"],
                    created_at=n["created_at"]
                ))
            db.commit()

        # Seed Travel Requests
        if db.query(TravelRequestDB).count() == 0:
            print("Seeding travel_requests table...")
            for tr in mock_db.travel_requests:
                db.add(TravelRequestDB(
                    id=tr["id"],
                    user_id=tr["user_id"],
                    destination=tr["destination"],
                    departure_date=datetime.date.fromisoformat(tr["departure_date"]),
                    return_date=datetime.date.fromisoformat(tr["return_date"]),
                    status=tr["status"],
                    selected_flight=tr["selected_flight"],
                    selected_hotel=tr["selected_hotel"]
                ))
            db.commit()

        # Seed Attendance Logs
        if db.query(AttendanceLogDB).count() == 0:
            print("Seeding attendance_logs table...")
            for al in mock_db.attendance_logs:
                db.add(AttendanceLogDB(
                    id=al["id"],
                    user_id=al["user_id"],
                    date=datetime.date.fromisoformat(al["date"]),
                    punch_in_at=al["punch_in_at"],
                    punch_out_at=al["punch_out_at"],
                    total_hours=al["total_hours"],
                    activity_log=al["activity_log"]
                ))
            db.commit()
            
        # Seed Skills
        if db.query(SkillDB).count() == 0:
            print("Seeding skills table...")
            for sk in mock_db.skills:
                db.add(SkillDB(
                    user_id=sk["user_id"],
                    skill_name=sk["skill_name"],
                    proficiency=sk["proficiency"],
                    category=sk["category"]
                ))
            db.commit()

        # Seed Certifications
        if db.query(CertificationDB).count() == 0:
            print("Seeding certifications table...")
            for c in mock_db.certifications:
                db.add(CertificationDB(
                    user_id=c["user_id"],
                    name=c["name"],
                    authority=c["authority"],
                    issued_date=datetime.date.fromisoformat(c["issued_date"]),
                    expiry_date=datetime.date.fromisoformat(c["expiry_date"]) if c["expiry_date"] != "#" else None,
                    url=c["url"]
                ))
            db.commit()

        # Seed OKRs
        if db.query(OkrDB).count() == 0:
            print("Seeding okrs table...")
            for ok in mock_db.okrs:
                db.add(OkrDB(
                    user_id=ok["user_id"],
                    type=ok["type"],
                    objective=ok["objective"],
                    key_results=ok["key_results"],
                    progress=ok["progress"],
                    year=ok["year"],
                    quarter=ok["quarter"]
                ))
            db.commit()

        # Seed Recognitions
        if db.query(RecognitionDB).count() == 0:
            print("Seeding recognitions table...")
            for r in mock_db.recognitions:
                db.add(RecognitionDB(
                    user_id=r["user_id"],
                    award_type=r["award_type"],
                    title=r["title"],
                    description=r["description"],
                    given_by=r["given_by"],
                    date=datetime.date.fromisoformat(r["date"])
                ))
            db.commit()

        # Seed Trainings
        if db.query(TrainingDB).count() == 0:
            print("Seeding trainings table...")
            for t in mock_db.trainings:
                db.add(TrainingDB(
                    user_id=t["user_id"],
                    course_name=t["course_name"],
                    provider=t["provider"],
                    status=t["status"],
                    progress=t["progress"],
                    recommended_by_ai=t["recommended_by_ai"]
                ))
            db.commit()

        # Seed Payroll
        if db.query(PayrollDB).count() == 0:
            print("Seeding payroll table...")
            db.add(PayrollDB(
                user_id=mock_db.payroll["user_id"],
                salary_base=mock_db.payroll["salary_base"],
                salary_allowance=mock_db.payroll["salary_allowance"],
                tax_deduction=mock_db.payroll["tax_deduction"],
                increment_history=mock_db.payroll["increment_history"],
                payslips=mock_db.payroll["payslips"]
            ))
            db.commit()

        # Seed Claims
        if db.query(ClaimDB).count() == 0:
            print("Seeding claims table...")
            for cl in mock_db.claims:
                db.add(ClaimDB(
                    user_id=cl["user_id"],
                    amount=cl["amount"],
                    category=cl["category"],
                    description=cl["description"],
                    date=datetime.date.fromisoformat(cl["date"]),
                    status=cl["status"]
                ))
            db.commit()

        # Seed Assets
        if db.query(AssetDB).count() == 0:
            print("Seeding assets table...")
            for a in mock_db.assets:
                db.add(AssetDB(
                    user_id=a["user_id"],
                    asset_name=a["asset_name"],
                    serial_number=a["serial_number"],
                    assigned_date=datetime.date.fromisoformat(a["assigned_date"]),
                    status=a["status"]
                ))
            db.commit()

        # Seed Announcements
        if db.query(AnnouncementDB).count() == 0:
            print("Seeding announcements table...")
            for an in mock_db.announcements:
                db.add(AnnouncementDB(
                    title=an["title"],
                    content=an["content"],
                    category=an["category"],
                    created_at=datetime.date.fromisoformat(an["created_at"])
                ))
            db.commit()

        # Seed Knowledge Base
        if db.query(KnowledgeBaseDB).count() == 0:
            print("Seeding knowledge base table...")
            for kb in mock_db.knowledge_base:
                db.add(KnowledgeBaseDB(
                    title=kb["title"],
                    category=kb["category"],
                    content=kb["content"],
                    url=kb["url"]
                ))
            db.commit()
            
        db.close()
        print("Database seeding completed.")
    except Exception as e:
        print(f"Error seeding database: {e}")
