import datetime
from typing import Dict, List, Any, Optional
import threading
from config import settings

# Initialize Supabase client if credentials exist
supabase_client = None
if not settings.is_mock_mode:
    try:
        from supabase import create_client, Client
        supabase_client: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    except Exception as e:
        print(f"Failed to connect to Supabase: {e}. Falling back to mock database.")

# Thread-safe in-memory mock database for mock mode
class MockDatabase:
    def __init__(self):
        self.lock = threading.Lock()
        
        # 1. Profiles
        # Debarati Patra is the logged-in employee. Manager is Saket Ranjan.
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
        
        # 2. Attendance Logs
        self.attendance_logs = [
            {
                "id": "att-1", 
                "user_id": "user-debarati", 
                "date": "2026-06-01", 
                "punch_in_at": "2026-06-01T09:00:00Z", 
                "punch_out_at": "2026-06-01T18:00:00Z", 
                "total_hours": 9.0,
                "activity_log": [{"time": "2026-06-01T09:00:00Z", "action": "Punch-In"}, {"time": "2026-06-01T18:00:00Z", "action": "Punch-Out"}]
            }
        ]
        
        # 3. Active Punch-in state (if user is punched in, track start time)
        self.active_punches: Dict[str, str] = {} # user_id -> punch_in_time string
        
        # 4. Timesheets
        self.timesheets = [
            {
                "id": "ts-1",
                "user_id": "user-debarati",
                "week_start": "2026-06-01", # Jun 1, 2026 - Jun 7, 2026
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
        
        # 5. Leaves
        self.leaves = [
            {
                "id": 1,
                "user_id": "user-debarati",
                "leave_type": "Other",
                "from_date": "2026-05-25",
                "to_date": "2026-05-25",
                "num_days": 1.0,
                "reason": "I had doctor's appointment in the morning.",
                "status": "Approved",
                "applied_date": "2026-05-27",
                "recalled": False
            },
            {
                "id": 2,
                "user_id": "user-debarati",
                "leave_type": "Sick Leave",
                "from_date": "2026-11-05",
                "to_date": "2026-11-05",
                "num_days": 1.0,
                "reason": "I am not feeling well.",
                "status": "Approved",
                "applied_date": "2026-11-05",
                "recalled": False
            },
            {
                "id": 3,
                "user_id": "user-debarati",
                "leave_type": "Other",
                "from_date": "2026-07-24",
                "to_date": "2026-07-24",
                "num_days": 1.0,
                "reason": "I will be traveling out of town.",
                "status": "Approved",
                "applied_date": "2026-07-24",
                "recalled": False
            },
            {
                "id": 4,
                "user_id": "user-debarati",
                "leave_type": "Other",
                "from_date": "2026-04-21",
                "to_date": "2026-04-21",
                "num_days": 0.5,
                "reason": "I live with my aunt and need to help her.",
                "status": "Approved",
                "applied_date": "2026-04-21",
                "recalled": False
            },
            {
                "id": 5,
                "user_id": "user-debarati",
                "leave_type": "Other",
                "from_date": "2026-03-30",
                "to_date": "2026-03-31",
                "num_days": 2.0,
                "reason": "My aunt who lives with me is sick.",
                "status": "Approved",
                "applied_date": "2026-03-31",
                "recalled": False
            },
            {
                "id": 6,
                "user_id": "user-debarati",
                "leave_type": "Other",
                "from_date": "2026-03-20",
                "to_date": "2026-03-20",
                "num_days": 0.5,
                "reason": "I got a call from bank regarding home loan verification.",
                "status": "Approved",
                "applied_date": "2026-03-19",
                "recalled": False
            },
            {
                "id": 7,
                "user_id": "user-debarati",
                "leave_type": "Other",
                "from_date": "2026-03-18",
                "to_date": "2026-03-18",
                "num_days": 1.0,
                "reason": "I have a doctor's appointment today.",
                "status": "Approved",
                "applied_date": "2026-03-17",
                "recalled": False
            },
            {
                "id": 8,
                "user_id": "user-debarati",
                "leave_type": "Other",
                "from_date": "2026-03-17",
                "to_date": "2026-03-17",
                "num_days": 1.0,
                "reason": "My aunt has an eye checkup.",
                "status": "Recalled",
                "applied_date": "2026-03-16",
                "recalled": True
            },
            {
                "id": 9,
                "user_id": "user-debarati",
                "leave_type": "Other",
                "from_date": "2026-03-03",
                "to_date": "2026-03-03",
                "num_days": 1.0,
                "reason": "Due to Holi celebration, traveling home.",
                "status": "Approved",
                "applied_date": "2026-02-03",
                "recalled": False
            }
        ]
        
        # 6. Holidays
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
        
        # 7. Policies
        self.policies = [
            {"id": 1, "title": "Employee Conduct & Integrity Guidelines", "category": "HR Policy", "url": "/policies/conduct.pdf", "published_at": "2025-01-10"},
            {"id": 2, "title": "Travel & Expense Reimbursement Policy v3.0", "category": "Finance", "url": "/policies/travel_policy.pdf", "published_at": "2025-08-15"},
            {"id": 3, "title": "IT Asset Allocation & Remote Work Policy", "category": "IT", "url": "/policies/it_asset.pdf", "published_at": "2026-02-01"},
            {"id": 4, "title": "Leave Policy Guidelines (2026)", "category": "HR Policy", "url": "/policies/leave_policy.pdf", "published_at": "2026-01-01"}
        ]
        
        # 8. Feedbacks & Performance Reviews
        self.feedbacks = [
            {
                "id": "fb-1",
                "user_id": "user-debarati",
                "reviewer_id": "user-saket",
                "feedback_type": "manager",
                "year": 2025,
                "rating_work_quality": 5,
                "rating_collaboration": 4,
                "rating_leadership": 4,
                "comments": "Debarati consistently delivers high quality solutions. She has demonstrated solid ownership of the decisions modules and provides valuable guidance to junior peers.",
                "project_ratings": {"Decisions": 4.8, "Client X": 4.5}
            },
            {
                "id": "fb-2",
                "user_id": "user-debarati",
                "reviewer_id": "user-abhyudaya",
                "feedback_type": "peer",
                "year": 2025,
                "rating_work_quality": 4,
                "rating_collaboration": 5,
                "rating_leadership": 4,
                "comments": "Great teammate to work with. Always helpful when resolving technical roadblocks in project integrations.",
                "project_ratings": {"Decisions": 4.5}
            },
            {
                "id": "fb-3",
                "user_id": "user-debarati",
                "reviewer_id": "user-anjana",
                "feedback_type": "peer",
                "year": 2025,
                "rating_work_quality": 5,
                "rating_collaboration": 4,
                "rating_leadership": 5,
                "comments": "Her architectural designs are highly sustainable. Highly professional and leads core initiatives effectively.",
                "project_ratings": {"Decisions": 5.0}
            }
        ]
        
        # 9. Promotions
        self.promotions = [
            {"id": "promo-1", "user_id": "user-debarati", "old_role": "Software Engineer", "new_role": "Senior Engineer", "date": "2023-04-01", "details": "Promoted for exceptional contributions in the client onboarding workflows."},
            {"id": "promo-2", "user_id": "user-debarati", "old_role": "Senior Engineer", "new_role": "Senior Consultant", "date": "2025-04-01", "details": "Promoted for leadership in platform revamps and decision system integration."}
        ]
        
        # 10. Travel Requests
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
        
        # 11. Notifications
        self.notifications = [
            {"id": "notif-1", "user_id": "user-debarati", "title": "Leave Approved", "message": "Your leave request for 25-05-2026 has been approved.", "read": False, "created_at": "2026-05-27T10:00:00Z"},
            {"id": "notif-2", "user_id": "user-debarati", "title": "Timesheet Submitted", "message": "Weekly timesheet (Jun 1 - Jun 7) submitted successfully.", "read": True, "created_at": "2026-06-02T11:00:00Z"},
            {"id": "notif-3", "user_id": "user-debarati", "title": "Yearly Performance Available", "message": "Your performance report for year 2025 is now active.", "read": False, "created_at": "2026-06-01T09:00:00Z"}
        ]

mock_db = MockDatabase()
