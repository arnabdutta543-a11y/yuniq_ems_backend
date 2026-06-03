import datetime
from typing import Dict, List, Any, Optional
import json
import os
from sqlalchemy import create_engine, Column, String, Integer, Float, Date, Boolean, JSON, ForeignKey, Numeric, Text, Index, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from config import settings

Base = declarative_base()

# SQLAlchemy Models

from sqlalchemy import TypeDecorator, DateTime
import datetime

class ISO8601DateTime(TypeDecorator):
    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, str):
            val_clean = value.replace("Z", "+00:00")
            return datetime.datetime.fromisoformat(val_clean)
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return value.isoformat().replace("+00:00", "") + "Z"

class ProfileDB(Base):
    __tablename__ = 'employees'
    id = Column(String(50), primary_key=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    role = Column(String(100), nullable=False)
    department = Column(String(100), nullable=False)
    manager_id = Column(String(50), ForeignKey('employees.id', ondelete='SET NULL'), nullable=True)
    salary = Column(Numeric, nullable=True)
    joining_date = Column(Date, nullable=True)
    personal_email = Column(String(100), nullable=True)
    office = Column(String(100), nullable=True)
    status = Column(String(50), nullable=True)
    password_hash = Column(String(200), nullable=True)
    assigned_laptop = Column(String(100), nullable=True)
    dob = Column(Date, nullable=True)
    gender = Column(String(10), nullable=True)
    address = Column(Text, nullable=True)
    contact_number = Column(String(20), nullable=True)
    bank_name = Column(String(100), nullable=True)
    account_number = Column(String(50), nullable=True)
    ifsc_code = Column(String(20), nullable=True)
    pan = Column(String(20), nullable=True)
    pf_number = Column(String(50), nullable=True)
    uan = Column(String(50), nullable=True)

    @property
    def avatar_url(self):
        return f"https://api.dicebear.com/7.x/adventurer/svg?seed={self.full_name}"

class AttendanceLogDB(Base):
    __tablename__ = 'attendance'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column("employee_id", String(50), ForeignKey('employees.id', ondelete='CASCADE'), nullable=False)
    date = Column(Date, nullable=False)
    punch_in_at = Column(ISO8601DateTime, nullable=False)
    punch_out_at = Column(ISO8601DateTime, nullable=True)
    total_hours = Column(Float, default=0.0)
    activity_log = Column(JSON, default=list)

    __table_args__ = (
        Index(
            'unique_active_attendance_session',
            'employee_id',
            'date',
            unique=True,
            postgresql_where=text("punch_out_at IS NULL")
        ),
    )

    def __init__(self, **kwargs):
        if 'id' in kwargs and isinstance(kwargs['id'], str) and kwargs['id'].startswith('att-'):
            kwargs.pop('id')
        super().__init__(**kwargs)

class TimesheetEntryDB(Base):
    __tablename__ = 'timesheet_entries'
    id = Column(Integer, primary_key=True, autoincrement=True)
    timesheet_id = Column(Integer, ForeignKey('timesheets.id', ondelete='CASCADE'), nullable=False)
    date = Column(Date, nullable=False)
    project = Column(String(50), nullable=False)
    hours = Column(Float, nullable=False)
    description = Column(Text, nullable=True)

class TimesheetDB(Base):
    __tablename__ = 'timesheets'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column("employee_id", String(50), ForeignKey('employees.id', ondelete='CASCADE'), nullable=False)
    week_start = Column(Date, nullable=False)
    status = Column(String(20), default='Draft')

    raw_entries = relationship("TimesheetEntryDB", cascade="all, delete-orphan", backref="timesheet")

    @property
    def entries(self):
        sorted_entries = sorted(self.raw_entries, key=lambda x: x.date)
        return [
            {
                "date": entry.date.isoformat(),
                "project": entry.project,
                "hours": float(entry.hours),
                "description": entry.description or ""
            }
            for entry in sorted_entries
        ]

    @entries.setter
    def entries(self, value_list):
        self.raw_entries.clear()
        for item in value_list:
            self.raw_entries.append(TimesheetEntryDB(
                date=datetime.date.fromisoformat(item["date"]),
                project=item["project"],
                hours=item["hours"],
                description=item.get("description", "")
            ))

    def __init__(self, **kwargs):
        entries_list = kwargs.pop('entries', [])
        if 'id' in kwargs and isinstance(kwargs['id'], str) and kwargs['id'].startswith('ts-'):
            kwargs.pop('id')
        super().__init__(**kwargs)
        if entries_list:
            self.entries = entries_list

class LeaveDB(Base):
    __tablename__ = 'leaves'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column("employee_id", String(50), ForeignKey('employees.id', ondelete='CASCADE'), nullable=False)
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
    location = Column(String(50), default='All')
    type = Column(String(20), default='National')

class PolicyDB(Base):
    __tablename__ = 'policies'
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(150), nullable=False)
    category = Column(String(50), nullable=False)
    url = Column(Text, nullable=False)
    published_at = Column(Date, nullable=False)

class FeedbackDB(Base):
    __tablename__ = 'performance_reviews'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column("employee_id", String(50), ForeignKey('employees.id', ondelete='CASCADE'), nullable=False)
    year = Column(Integer, nullable=False)
    rating_work_quality = Column("quality_rating", Float, nullable=False)
    rating_collaboration = Column("collaboration_rating", Float, nullable=False)
    rating_leadership = Column("leadership_rating", Float, nullable=False)
    comments = Column("manager_comments", Text, nullable=True)

    @property
    def feedback_type(self):
        return 'manager'

    @property
    def reviewer_id(self):
        return 'user-saket'

    @property
    def project_ratings(self):
        return {"Decisions": float(self.rating_work_quality or 4.5)}

    def __init__(self, **kwargs):
        kwargs.pop('id', None)
        kwargs.pop('reviewer_id', None)
        kwargs.pop('feedback_type', None)
        kwargs.pop('project_ratings', None)
        if 'rating_work_quality' not in kwargs and 'quality_rating' in kwargs:
            kwargs['rating_work_quality'] = kwargs.pop('quality_rating')
        if 'rating_collaboration' not in kwargs and 'collaboration_rating' in kwargs:
            kwargs['rating_collaboration'] = kwargs.pop('collaboration_rating')
        if 'rating_leadership' not in kwargs and 'leadership_rating' in kwargs:
            kwargs['rating_leadership'] = kwargs.pop('leadership_rating')
        if 'comments' not in kwargs and 'manager_comments' in kwargs:
            kwargs['comments'] = kwargs.pop('manager_comments')
        super().__init__(**kwargs)

class PromotionDB(Base):
    __tablename__ = 'promotions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column("employee_id", String(50), ForeignKey('employees.id', ondelete='CASCADE'), nullable=False)
    old_role = Column(String(100), nullable=False)
    new_role = Column(String(100), nullable=False)
    date = Column(Date, nullable=False)
    details = Column(Text, nullable=True)

    def __init__(self, **kwargs):
        if 'id' in kwargs and isinstance(kwargs['id'], str) and kwargs['id'].startswith('promo-'):
            kwargs.pop('id')
        super().__init__(**kwargs)

class TravelRequestDB(Base):
    __tablename__ = 'travel_requests'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column("employee_id", String(50), ForeignKey('employees.id', ondelete='CASCADE'), nullable=False)
    destination = Column(String(100), nullable=False)
    departure_date = Column(Date, nullable=False)
    return_date = Column(Date, nullable=False)
    status = Column(String(30), default='Pending Approval')
    selected_flight = Column(JSON, nullable=True)
    selected_hotel = Column(JSON, nullable=True)

    def __init__(self, **kwargs):
        if 'id' in kwargs and isinstance(kwargs['id'], str) and kwargs['id'].startswith('travel-'):
            kwargs.pop('id')
        super().__init__(**kwargs)

class NotificationDB(Base):
    __tablename__ = 'notifications'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column("employee_id", String(50), ForeignKey('employees.id', ondelete='CASCADE'), nullable=False)
    title = Column(String(150), nullable=False)
    message = Column(Text, nullable=False)
    read = Column(Boolean, default=False)
    created_at = Column(ISO8601DateTime, nullable=False)

    def __init__(self, **kwargs):
        if 'id' in kwargs and isinstance(kwargs['id'], str) and kwargs['id'].startswith('notif-'):
            kwargs.pop('id')
        super().__init__(**kwargs)

class SkillDB(Base):
    __tablename__ = 'skills'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column("employee_id", String(50), ForeignKey('employees.id', ondelete='CASCADE'), nullable=False)
    skill_name = Column(String(100), nullable=False)
    proficiency = Column(Integer, nullable=False)
    category = Column(String(50), nullable=False)

class CertificationDB(Base):
    __tablename__ = 'certifications'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column("employee_id", String(50), ForeignKey('employees.id', ondelete='CASCADE'), nullable=False)
    name = Column(String(150), nullable=False)
    authority = Column(String(100), nullable=False)
    issued_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=True)
    url = Column(Text, nullable=True)

class OkrDB(Base):
    __tablename__ = 'okrs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column("employee_id", String(50), ForeignKey('employees.id', ondelete='CASCADE'), nullable=False)
    type = Column(String(20), nullable=False)
    objective = Column(Text, nullable=False)
    key_results = Column(JSON, nullable=False)
    progress = Column(Float, default=0.0)
    year = Column(Integer, nullable=False)
    quarter = Column(Integer, nullable=False)

class RecognitionDB(Base):
    __tablename__ = 'recognitions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column("employee_id", String(50), ForeignKey('employees.id', ondelete='CASCADE'), nullable=False)
    award_type = Column(String(50), nullable=False)
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=False)
    given_by = Column(String(100), nullable=False)
    date = Column(Date, nullable=False)

class TrainingDB(Base):
    __tablename__ = 'trainings'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column("employee_id", String(50), ForeignKey('employees.id', ondelete='CASCADE'), nullable=False)
    course_name = Column(String(150), nullable=False)
    provider = Column(String(100), nullable=False)
    status = Column(String(30), nullable=False)
    progress = Column(Float, default=0.0)
    recommended_by_ai = Column(Boolean, default=False)

class PayrollDB(Base):
    __tablename__ = 'payslips'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column("employee_id", String(50), ForeignKey('employees.id', ondelete='CASCADE'), nullable=False)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    salary_base = Column("basic_salary", Float, nullable=False)
    salary_allowance = Column("allowances", Float, nullable=False)
    tax_deduction = Column("deductions", Float, nullable=False)
    net = Column("net_salary", Float, nullable=False)
    status = Column(String(20), default='Paid')
    paid_days = Column(Integer, default=30)
    lop_days = Column(Integer, default=0)
    leave_balance = Column(Float, default=10.5)

class ClaimDB(Base):
    __tablename__ = 'claims'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column("employee_id", String(50), ForeignKey('employees.id', ondelete='CASCADE'), nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    date = Column(Date, nullable=False)
    status = Column(String(20), default='Pending')

class AssetDB(Base):
    __tablename__ = 'resources'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column("employee_id", String(50), ForeignKey('employees.id', ondelete='CASCADE'), nullable=True)
    asset_name = Column("name", String(150), nullable=False)
    serial_number = Column(String(100), nullable=False)
    status = Column(String(30), default='Assigned')

class AssetRequestDB(Base):
    __tablename__ = 'asset_requests'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column("employee_id", String(50), ForeignKey('employees.id', ondelete='CASCADE'), nullable=False)
    request_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(30), default='Submitted')
    created_at = Column(ISO8601DateTime, nullable=False)
    admin_notes = Column(Text, nullable=True)

    @property
    def assigned_date(self):
        return datetime.date(2025, 10, 15)

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

        # Ensure new columns and unique active index exist in PostgreSQL (dynamic ALTERs)
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE employees ADD COLUMN IF NOT EXISTS dob DATE;"))
            conn.execute(text("ALTER TABLE employees ADD COLUMN IF NOT EXISTS gender VARCHAR(10) DEFAULT 'Female';"))
            conn.execute(text("ALTER TABLE employees ADD COLUMN IF NOT EXISTS address TEXT;"))
            conn.execute(text("ALTER TABLE employees ADD COLUMN IF NOT EXISTS contact_number VARCHAR(20);"))
            conn.execute(text("ALTER TABLE employees ADD COLUMN IF NOT EXISTS bank_name VARCHAR(100);"))
            conn.execute(text("ALTER TABLE employees ADD COLUMN IF NOT EXISTS account_number VARCHAR(50);"))
            conn.execute(text("ALTER TABLE employees ADD COLUMN IF NOT EXISTS ifsc_code VARCHAR(20);"))
            conn.execute(text("ALTER TABLE employees ADD COLUMN IF NOT EXISTS pan VARCHAR(20);"))
            conn.execute(text("ALTER TABLE employees ADD COLUMN IF NOT EXISTS pf_number VARCHAR(50);"))
            conn.execute(text("ALTER TABLE employees ADD COLUMN IF NOT EXISTS uan VARCHAR(50);"))
            
            conn.execute(text("ALTER TABLE payslips ADD COLUMN IF NOT EXISTS paid_days INTEGER DEFAULT 30;"))
            conn.execute(text("ALTER TABLE payslips ADD COLUMN IF NOT EXISTS lop_days INTEGER DEFAULT 0;"))
            conn.execute(text("ALTER TABLE payslips ADD COLUMN IF NOT EXISTS leave_balance FLOAT DEFAULT 10.5;"))
            
            conn.execute(text("ALTER TABLE holidays ADD COLUMN IF NOT EXISTS location VARCHAR(50) DEFAULT 'All';"))
            conn.execute(text("ALTER TABLE holidays ADD COLUMN IF NOT EXISTS type VARCHAR(20) DEFAULT 'National';"))
            
            conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS unique_active_attendance_session ON attendance (employee_id, date) WHERE punch_out_at IS NULL;"))
            
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS asset_requests (
                    id SERIAL PRIMARY KEY,
                    employee_id VARCHAR(50) NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
                    request_type VARCHAR(50) NOT NULL,
                    description TEXT NOT NULL,
                    status VARCHAR(30) DEFAULT 'Submitted',
                    created_at TIMESTAMP NOT NULL,
                    admin_notes TEXT
                );
            """))
            conn.commit()
        print("Raw DDL migrations executed successfully.")
        
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
                    manager_id=p["manager_id"],
                    dob=datetime.date(1995, 5, 15) if p["id"] == "user-debarati" else datetime.date(1990, 8, 20),
                    gender="Female" if p["id"] in ["user-debarati", "user-debolina", "user-anjana", "user-annesha"] else "Male",
                    address="123 Chennai Main Rd, OMR, Chennai, TN" if p["id"] == "user-debarati" else "456 OMR Road, Bangalore, KA",
                    contact_number="+91 98765 43210" if p["id"] == "user-debarati" else "+91 99999 88888",
                    bank_name="HDFC Bank" if p["id"] == "user-debarati" else "ICICI Bank",
                    account_number="50100432109876" if p["id"] == "user-debarati" else "304561237890",
                    ifsc_code="HDFC0000123" if p["id"] == "user-debarati" else "ICIC0003045",
                    pan="ABCDE1234F" if p["id"] == "user-debarati" else "XYZW9876C",
                    pf_number="TN/MAS/0012345/000/0001234" if p["id"] == "user-debarati" else "KA/BLR/0098765/000/0005678",
                    uan="100123456789" if p["id"] == "user-debarati" else "100987654321",
                    office="Chennai" if p["id"] == "user-debarati" else "Bangalore"
                ))
            db.commit()

        # Update existing user-debarati profile with detail columns if they are null
        debarati = db.query(ProfileDB).filter(ProfileDB.id == 'user-debarati').first()
        if debarati and not debarati.bank_name:
            print("Updating user-debarati's detailed profile fields...")
            debarati.dob = datetime.date(1995, 5, 15)
            debarati.gender = "Female"
            debarati.address = "123 Chennai Main Rd, OMR, Chennai, TN"
            debarati.contact_number = "+91 98765 43210"
            debarati.bank_name = "HDFC Bank"
            debarati.account_number = "50100432109876"
            debarati.ifsc_code = "HDFC0000123"
            debarati.pan = "ABCDE1234F"
            debarati.pf_number = "TN/MAS/0012345/000/0001234"
            debarati.uan = "100123456789"
            debarati.office = "Chennai"
            db.commit()
            
        # Seed Holidays
        if db.query(HolidayDB).count() == 0:
            print("Seeding holidays table...")
            holiday_details = [
                {"name": "New Year's Day", "date": "2026-01-01", "day": "Thu", "location": "All", "type": "National"},
                {"name": "Pongal", "date": "2026-01-14", "day": "Wed", "location": "Chennai", "type": "State"},
                {"name": "Republic Day", "date": "2026-01-26", "day": "Mon", "location": "All", "type": "National"},
                {"name": "Makar Sankranti", "date": "2026-01-14", "day": "Wed", "location": "Bangalore", "type": "State"},
                {"name": "Karnataka Rajyotsava", "date": "2026-11-01", "day": "Sun", "location": "Bangalore", "type": "State"},
                {"name": "Independence Day", "date": "2026-08-15", "day": "Sat", "location": "All", "type": "National"},
                {"name": "Ganesh Chaturthi", "date": "2026-09-14", "day": "Mon", "location": "Mumbai", "type": "State"},
                {"name": "Founders Day", "date": "2026-10-15", "day": "Thu", "location": "All", "type": "Organization"},
                {"name": "Gandhi Jayanthi", "date": "2026-10-02", "day": "Fri", "location": "All", "type": "National"},
                {"name": "Christmas", "date": "2026-12-25", "day": "Fri", "location": "All", "type": "National"}
            ]
            for h in holiday_details:
                db.add(HolidayDB(
                    name=h["name"],
                    date=datetime.date.fromisoformat(h["date"]),
                    day=h["day"],
                    location=h["location"],
                    type=h["type"]
                ))
            db.commit()
            
        # Backfill location/type for existing holidays if they are empty
        with engine.connect() as conn:
            conn.execute(text("UPDATE holidays SET location = 'All', type = 'National' WHERE location IS NULL OR type IS NULL;"))
            conn.execute(text("""
                INSERT INTO holidays (name, date, day, location, type) 
                SELECT 'Pongal', '2026-01-14', 'Wed', 'Chennai', 'State'
                WHERE NOT EXISTS (SELECT 1 FROM holidays WHERE name = 'Pongal' AND location = 'Chennai');
            """))
            conn.execute(text("""
                INSERT INTO holidays (name, date, day, location, type) 
                SELECT 'Karnataka Rajyotsava', '2026-11-01', 'Sun', 'Bangalore', 'State'
                WHERE NOT EXISTS (SELECT 1 FROM holidays WHERE name = 'Karnataka Rajyotsava' AND location = 'Bangalore');
            """))
            conn.execute(text("""
                INSERT INTO holidays (name, date, day, location, type) 
                SELECT 'Founders Day', '2026-10-15', 'Thu', 'All', 'Organization'
                WHERE NOT EXISTS (SELECT 1 FROM holidays WHERE name = 'Founders Day');
            """))
            conn.commit()
            
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
