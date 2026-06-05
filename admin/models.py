import datetime
from sqlalchemy import (
    Column,
    String,
    Integer,
    Numeric,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Text,
    JSON,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from admin.database import Base


class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, unique=True, index=True, nullable=False)


class Department(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, unique=True, index=True, nullable=False)


class Office(Base):
    __tablename__ = "offices"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, unique=True, index=True, nullable=False)


class Announcement(Base):
    __tablename__ = "announcements"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String, nullable=False)
    created_at = Column(Date, default=datetime.date.today, nullable=False)


class Policy(Base):
    __tablename__ = "policies"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String, nullable=False)
    category = Column(String, nullable=False)
    url = Column(Text, nullable=False)
    published_at = Column(Date, default=datetime.date.today, nullable=False)


class Holiday(Base):
    __tablename__ = "holidays"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    day = Column(String, nullable=False)
    office = Column(String, default="All", nullable=False)  # Kolkata, Chennai, All


class Employee(Base):
    __tablename__ = "employees"

    id = Column(String, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    role = Column(String, nullable=False)
    department = Column(String, nullable=False)
    manager_id = Column(String, ForeignKey("employees.id"), nullable=True)
    salary = Column(Numeric(12, 2), nullable=True)
    joining_date = Column(Date, nullable=True)
    personal_email = Column(String, nullable=True)
    office = Column(String, default="Kolkata", nullable=False)
    status = Column(String, default="Pending", nullable=False)  # Pending, Active
    password_hash = Column(String, nullable=True)
    assigned_laptop = Column(String, nullable=True)
    permissions = Column(Text, nullable=True)  # JSON array of permissions
    dob = Column(Date, nullable=True)
    gender = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    contact_number = Column(String, nullable=True)
    bank_name = Column(String, nullable=True)
    account_number = Column(String, nullable=True)
    ifsc_code = Column(String, nullable=True)
    pan = Column(String, nullable=True)
    pf_number = Column(String, nullable=True)
    uan = Column(String, nullable=True)
    admin_portal_access = Column(Boolean, default=False, nullable=False)
    paid_leaves = Column(Integer, default=24, nullable=False)
    leave_balance = Column(Integer, default=24, nullable=False)
    lop_days = Column(Integer, default=0, nullable=False)
    leave_year = Column(Integer, default=datetime.date.today().year, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

    # Relationships
    manager = relationship("Employee", remote_side=[id], backref="subordinates")
    leaves = relationship("Leave", back_populates="employee", cascade="all, delete-orphan")
    timesheets = relationship("Timesheet", back_populates="employee", cascade="all, delete-orphan")
    attendance_logs = relationship("Attendance", back_populates="employee", cascade="all, delete-orphan")
    travel_requests = relationship("TravelRequest", back_populates="employee", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="employee", cascade="all, delete-orphan")
    performance_reviews = relationship("PerformanceReview", back_populates="employee", cascade="all, delete-orphan")
    invitations = relationship("OnboardingInvitation", back_populates="employee", cascade="all, delete-orphan")
    payslips = relationship("Payslip", back_populates="employee", cascade="all, delete-orphan")
    recognitions_received = relationship("Recognition", foreign_keys="Recognition.employee_id", back_populates="employee", cascade="all, delete-orphan")
    recognitions_given = relationship("Recognition", foreign_keys="Recognition.given_by_id", back_populates="given_by")
    trainings = relationship("Training", back_populates="employee", cascade="all, delete-orphan")
    asset_requests = relationship("AssetRequest", foreign_keys="AssetRequest.employee_id", back_populates="employee", cascade="all, delete-orphan")
    okrs = relationship("OKR", back_populates="employee", cascade="all, delete-orphan")

    @property
    def resolved_permissions(self):
        if not self.admin_portal_access and self.email != "admin@yuniq.com":
            return []
        import json
        if self.permissions:
            try:
                return json.loads(self.permissions)
            except Exception:
                pass

        # Role-based default fallbacks
        role = self.role
        if not role:
            return []

        role_lower = role.lower()
        if (role in ["CEO", "HR Manager", "Admin"] or
                self.email == "admin@yuniq.com" or
                "ceo" in role_lower or
                ("hr" in role_lower and "manager" in role_lower)):
            return [
                "tabs.dashboard", "tabs.employees", "tabs.invitations", "tabs.leaves",
                "tabs.timesheets", "tabs.travel", "tabs.performance", "tabs.payslips",
                "tabs.holidays", "tabs.resources", "tabs.config", "tabs.notifications",
                "tabs.recognitions", "tabs.trainings", "tabs.asset_requests", "tabs.policies",
                "actions.manage_employees", "actions.add_employee", "actions.edit_employee", "actions.delete_employee", "actions.view_employee_details",
                "actions.manage_invitations", "actions.manage_leaves",
                "actions.manage_timesheets", "actions.manage_travel", "actions.manage_performance",
                "actions.manage_payslips", "actions.manage_holidays", "actions.manage_resources",
                "actions.manage_config", "actions.manage_notifications", "actions.manage_recognitions",
                "actions.manage_trainings", "actions.manage_asset_requests", "actions.manage_policies"
            ]
        elif "hr" in role_lower or "recruit" in role_lower or "talent" in role_lower:
            return [
                "tabs.dashboard", "tabs.employees", "tabs.invitations", "tabs.leaves",
                "tabs.timesheets", "tabs.travel", "tabs.performance", "tabs.payslips",
                "tabs.holidays", "tabs.resources", "tabs.config", "tabs.notifications",
                "tabs.recognitions", "tabs.trainings", "tabs.asset_requests", "tabs.policies",
                "actions.manage_employees", "actions.add_employee", "actions.edit_employee", "actions.delete_employee", "actions.view_employee_details",
                "actions.manage_invitations", "actions.manage_leaves",
                "actions.manage_timesheets", "actions.manage_travel", "actions.manage_performance",
                "actions.manage_payslips", "actions.manage_holidays", "actions.manage_resources",
                "actions.manage_config", "actions.manage_notifications", "actions.manage_recognitions",
                "actions.manage_trainings", "actions.manage_asset_requests", "actions.manage_policies"
            ]
        elif role == "IT-admin" or "it" in role_lower or "system" in role_lower or "network" in role_lower or "asset" in role_lower:
            return [
                "tabs.dashboard", "tabs.holidays", "tabs.resources",
                "tabs.trainings", "tabs.asset_requests", "tabs.policies",
                "actions.manage_resources", "actions.manage_holidays",
                "actions.manage_trainings", "actions.manage_asset_requests"
            ]
        elif (role in ["Director", "Manager", "Senior Manager", "Management"] or
              "manager" in role_lower or
              "director" in role_lower or
              "management" in role_lower or
              "lead" in role_lower or
              "head" in role_lower or
              "vp" in role_lower):
            is_director = role == "Director" or "director" in role_lower
            policy_actions = ["actions.manage_policies"] if is_director else []
            return [
                "tabs.dashboard", "tabs.employees", "tabs.leaves", "tabs.timesheets",
                "tabs.travel", "tabs.performance", "tabs.payslips", "tabs.holidays", "tabs.notifications",
                "tabs.recognitions", "tabs.trainings", "tabs.asset_requests", "tabs.policies",
                "actions.view_employee_details",
                "actions.manage_leaves", "actions.manage_timesheets", "actions.manage_travel",
                "actions.manage_performance", "actions.manage_notifications", "actions.manage_recognitions",
                "actions.manage_trainings"
            ] + policy_actions
        return []


class Recognition(Base):
    __tablename__ = "recognitions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    employee_id = Column(String, ForeignKey("employees.id"), nullable=False)
    given_by_id = Column(String, ForeignKey("employees.id"), nullable=False)
    award_type = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    date = Column(Date, default=datetime.date.today, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    employee = relationship("Employee", foreign_keys=[employee_id], back_populates="recognitions_received")
    given_by = relationship("Employee", foreign_keys=[given_by_id], back_populates="recognitions_given")


class Training(Base):
    __tablename__ = "trainings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    employee_id = Column(String, ForeignKey("employees.id"), nullable=False)
    course_name = Column(String, nullable=False)
    provider = Column(String, nullable=True)
    status = Column(String, default="Not Started", nullable=False)
    progress = Column(Integer, default=0, nullable=False)
    completion_date = Column(Date, nullable=True)
    recommended_by_ai = Column(Boolean, default=False, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

    employee = relationship("Employee", back_populates="trainings")


class AssetRequest(Base):
    __tablename__ = "asset_requests"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    employee_id = Column(String, ForeignKey("employees.id"), nullable=False)
    item_name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(String, default="Normal", nullable=False)
    status = Column(String, default="Pending", nullable=False)
    it_response = Column(Text, nullable=True)
    reviewed_by_id = Column(String, ForeignKey("employees.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

    employee = relationship("Employee", foreign_keys=[employee_id], back_populates="asset_requests")
    reviewed_by = relationship("Employee", foreign_keys=[reviewed_by_id])


class Resource(Base):
    __tablename__ = "resources"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    asset_id = Column(String, unique=True, index=True, nullable=False)
    serial_number = Column(String, nullable=True)
    specifications = Column(Text, nullable=True)
    employee_id = Column(String, ForeignKey("employees.id", ondelete="SET NULL"), nullable=True)
    status = Column(String, default="Available", nullable=False)

    employee = relationship("Employee", backref="assigned_resources")


class Leave(Base):
    __tablename__ = "leaves"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    employee_id = Column(String, ForeignKey("employees.id"), nullable=False)
    leave_type = Column(String, nullable=False)
    from_date = Column(Date, nullable=False)
    to_date = Column(Date, nullable=False)
    num_days = Column(Numeric(4, 1), nullable=False)
    reason = Column(Text, nullable=True)
    status = Column(String, default="Pending", nullable=False)
    applied_date = Column(Date, default=datetime.date.today, nullable=False)
    recalled = Column(Boolean, default=False, nullable=False)

    employee = relationship("Employee", back_populates="leaves")


class Timesheet(Base):
    __tablename__ = "timesheets"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    employee_id = Column(String, ForeignKey("employees.id"), nullable=False)
    week_start = Column(Date, nullable=False)
    status = Column(String, default="Draft", nullable=False)

    employee = relationship("Employee", back_populates="timesheets")
    entries = relationship("TimesheetEntry", back_populates="timesheet", cascade="all, delete-orphan")


class TimesheetEntry(Base):
    __tablename__ = "timesheet_entries"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timesheet_id = Column(Integer, ForeignKey("timesheets.id"), nullable=False)
    date = Column(Date, nullable=False)
    project = Column(String, nullable=False)
    hours = Column(Numeric(4, 1), nullable=False)
    description = Column(Text, nullable=True)

    timesheet = relationship("Timesheet", back_populates="entries")


class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    employee_id = Column(String, ForeignKey("employees.id"), nullable=False)
    date = Column(Date, nullable=False)
    punch_in_at = Column(DateTime, nullable=False)
    punch_out_at = Column(DateTime, nullable=True)
    total_hours = Column(Numeric(5, 2), default=0.0, nullable=False)
    activity_log = Column(JSONB, default=list, nullable=False)

    employee = relationship("Employee", back_populates="attendance_logs")


class TravelRequest(Base):
    __tablename__ = "travel_requests"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    employee_id = Column(String, ForeignKey("employees.id"), nullable=False)
    destination = Column(String, nullable=False)
    departure_date = Column(Date, nullable=False)
    return_date = Column(Date, nullable=False)
    status = Column(String, default="Pending Approval", nullable=False)
    selected_flight = Column(JSONB, nullable=True)
    selected_hotel = Column(JSONB, nullable=True)

    employee = relationship("Employee", back_populates="travel_requests")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    employee_id = Column(String, ForeignKey("employees.id"), nullable=False)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    employee = relationship("Employee", back_populates="notifications")


class PerformanceReview(Base):
    __tablename__ = "performance_reviews"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    employee_id = Column(String, ForeignKey("employees.id"), nullable=False)
    year = Column(Integer, nullable=False)
    quality_rating = Column(Numeric(3, 2), nullable=False)
    collaboration_rating = Column(Numeric(3, 2), nullable=False)
    leadership_rating = Column(Numeric(3, 2), nullable=False)
    manager_comments = Column(Text, nullable=True)

    employee = relationship("Employee", back_populates="performance_reviews")


class OnboardingInvitation(Base):
    __tablename__ = "onboarding_invitations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    employee_id = Column(String, ForeignKey("employees.id"), nullable=False)
    email = Column(String, nullable=False)
    invitation_token = Column(String, unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    employee = relationship("Employee", back_populates="invitations")


class Payslip(Base):
    __tablename__ = "payslips"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    employee_id = Column(String, ForeignKey("employees.id"), nullable=False)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    basic_salary = Column(Numeric(12, 2), nullable=False)
    allowances = Column(Numeric(12, 2), nullable=False)
    deductions = Column(Numeric(12, 2), nullable=False)
    net_salary = Column(Numeric(12, 2), nullable=False)
    status = Column(String, default="Paid", nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    employee = relationship("Employee", back_populates="payslips")


class OKR(Base):
    __tablename__ = "okrs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    employee_id = Column(String, ForeignKey("employees.id"), nullable=False)
    type = Column(String, nullable=False)
    objective = Column(Text, nullable=False)
    key_results = Column(JSON, nullable=False)
    progress = Column(Numeric(5, 2), nullable=True)
    year = Column(Integer, nullable=False)
    quarter = Column(Integer, nullable=False)
    due_date = Column(Date, nullable=True)
    success_criteria = Column(Text, nullable=True)
    assigned_by = Column(String, nullable=True)
    evidence_url = Column(Text, nullable=True)
    completion_remarks = Column(Text, nullable=True)
    appraisal_submitted = Column(Boolean, default=False)
    appraisal_summary = Column(Text, nullable=True)
    appraisal_evidence = Column(Text, nullable=True)
    previous_ctc = Column(Numeric(12, 2), nullable=True)
    current_ctc = Column(Numeric(12, 2), nullable=True)
    appraisal_percentage = Column(Numeric(5, 2), nullable=True)

    employee = relationship("Employee", back_populates="okrs")
