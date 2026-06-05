from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Any
from datetime import date, datetime
from decimal import Decimal

# Dynamic configuration lists
class RoleBase(BaseModel):
    name: str

class RoleCreate(RoleBase):
    pass

class RoleOut(RoleBase):
    id: int
    class Config:
        from_attributes = True

class DepartmentBase(BaseModel):
    name: str

class DepartmentCreate(DepartmentBase):
    pass

class DepartmentOut(DepartmentBase):
    id: int
    class Config:
        from_attributes = True

class OfficeBase(BaseModel):
    name: str

class OfficeCreate(OfficeBase):
    pass

class OfficeOut(OfficeBase):
    id: int
    class Config:
        from_attributes = True

# Holiday schemas
class HolidayBase(BaseModel):
    name: str
    date: date
    day: str
    office: str = "All"

class HolidayCreate(HolidayBase):
    pass

class HolidayOut(HolidayBase):
    id: int
    class Config:
        from_attributes = True

# Payslip schemas
class PayslipBase(BaseModel):
    employee_id: str
    month: int = Field(..., ge=1, le=12)
    year: int
    basic_salary: Decimal
    allowances: Decimal
    deductions: Decimal
    net_salary: Decimal
    status: str = "Paid"

class PayslipCreate(PayslipBase):
    pass

class PayslipOut(PayslipBase):
    id: int
    employee_name: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True

# Auth schemas
class UserSignUp(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class UserSignIn(BaseModel):
    email: EmailStr
    password: str

# Employee Schemas
class EmployeeBase(BaseModel):
    full_name: str
    email: EmailStr
    role: str
    department: str
    manager_id: Optional[str] = None
    salary: Optional[Decimal] = None
    joining_date: Optional[date] = None
    personal_email: Optional[EmailStr] = None
    office: str = "Kolkata"
    assigned_laptop: Optional[str] = None
    permissions: Optional[List[str]] = None
    dob: Optional[date] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    contact_number: Optional[str] = None
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    ifsc_code: Optional[str] = None
    pan: Optional[str] = None
    pf_number: Optional[str] = None
    uan: Optional[str] = None
    admin_portal_access: bool = False
    paid_leaves: int = 24
    leave_balance: int = 24
    lop_days: int = 0
    leave_year: Optional[int] = None

class EmployeeCreate(EmployeeBase):
    custom_id: Optional[str] = None

class EmployeeUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    department: Optional[str] = None
    manager_id: Optional[str] = None
    salary: Optional[Decimal] = None
    joining_date: Optional[date] = None
    personal_email: Optional[EmailStr] = None
    office: Optional[str] = None
    status: Optional[str] = None
    assigned_laptop: Optional[str] = None
    permissions: Optional[List[str]] = None
    dob: Optional[date] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    contact_number: Optional[str] = None
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    ifsc_code: Optional[str] = None
    pan: Optional[str] = None
    pf_number: Optional[str] = None
    uan: Optional[str] = None
    admin_portal_access: Optional[bool] = None
    paid_leaves: Optional[int] = None
    leave_balance: Optional[int] = None
    lop_days: Optional[int] = None
    leave_year: Optional[int] = None

class EmployeeOut(EmployeeBase):
    id: str
    status: str
    created_at: datetime
    updated_at: datetime
    permissions: List[str] = Field(default=[], validation_alias="resolved_permissions")

    class Config:
        from_attributes = True

# Bank Details Schemas
class BankDetailsBase(BaseModel):
    bank_name: str
    account_number: str
    ifsc_code: str
    account_type: str = "Savings"

class BankDetailsCreate(BankDetailsBase):
    employee_id: str

class BankDetailsOut(BankDetailsBase):
    id: int
    employee_id: str
    created_at: datetime
    class Config:
        from_attributes = True

# PAN Info Schemas
class PANInfoBase(BaseModel):
    pan_number: Optional[str] = None
    pf_number: Optional[str] = None
    uan_number: Optional[str] = None

class PANInfoCreate(PANInfoBase):
    employee_id: str

class PANInfoOut(PANInfoBase):
    id: int
    employee_id: str
    created_at: datetime
    class Config:
        from_attributes = True

# Leave Schemas
class LeaveOut(BaseModel):
    id: int
    employee_id: str
    employee_name: Optional[str] = None
    leave_type: str
    from_date: date
    to_date: date
    num_days: Decimal
    reason: Optional[str] = None
    status: str
    applied_date: date
    recalled: bool

    class Config:
        from_attributes = True

class LeaveSummaryOut(BaseModel):
    employee_id: str
    employee_name: str
    paid_leaves: int
    leaves_taken: int
    leave_balance: int
    lop_days: int
    leave_year: int
    carry_forward: int
    leave_history: List[LeaveOut] = []

    class Config:
        from_attributes = True

class LeaveStatusUpdate(BaseModel):
    status: str

# Timesheet Schemas
class TimesheetEntryBase(BaseModel):
    date: date
    project: str
    hours: Decimal
    description: Optional[str] = None

class TimesheetEntryOut(TimesheetEntryBase):
    id: int
    timesheet_id: int

    class Config:
        from_attributes = True

class TimesheetOut(BaseModel):
    id: int
    employee_id: str
    employee_name: Optional[str] = None
    week_start: date
    status: str
    entries: List[TimesheetEntryOut] = []

    class Config:
        from_attributes = True

# Travel Schemas
class TravelRequestOut(BaseModel):
    id: int
    employee_id: str
    employee_name: Optional[str] = None
    destination: str
    departure_date: date
    return_date: date
    status: str
    selected_flight: Optional[Any] = None
    selected_hotel: Optional[Any] = None

    class Config:
        from_attributes = True

# Performance Review Schemas
class PerformanceReviewCreate(BaseModel):
    employee_id: str
    year: int
    quality_rating: Decimal = Field(..., ge=0, le=5)
    collaboration_rating: Decimal = Field(..., ge=0, le=5)
    leadership_rating: Decimal = Field(..., ge=0, le=5)
    manager_comments: Optional[str] = None

class PerformanceReviewUpdate(BaseModel):
    year: Optional[int] = None
    quality_rating: Optional[Decimal] = Field(None, ge=0, le=5)
    collaboration_rating: Optional[Decimal] = Field(None, ge=0, le=5)
    leadership_rating: Optional[Decimal] = Field(None, ge=0, le=5)
    manager_comments: Optional[str] = None

class PerformanceReviewOut(PerformanceReviewCreate):
    id: int

    class Config:
        from_attributes = True

# Recognition Schemas
class RecognitionCreate(BaseModel):
    employee_id: str
    given_by_id: str
    award_type: str
    title: str
    description: Optional[str] = None
    date: Optional[date] = None

class RecognitionOut(BaseModel):
    id: int
    employee_id: str
    given_by_id: str
    award_type: str
    title: str
    description: Optional[str] = None
    date: date
    created_at: datetime
    employee_name: Optional[str] = None
    given_by_name: Optional[str] = None

    class Config:
        from_attributes = True

# Training Schemas
class TrainingCreate(BaseModel):
    employee_id: str
    course_name: str
    provider: Optional[str] = None
    status: str = "Not Started"
    progress: int = Field(default=0, ge=0, le=100)
    completion_date: Optional[date] = None
    recommended_by_ai: bool = False
    notes: Optional[str] = None

class TrainingUpdate(BaseModel):
    course_name: Optional[str] = None
    provider: Optional[str] = None
    status: Optional[str] = None
    progress: Optional[int] = Field(None, ge=0, le=100)
    completion_date: Optional[date] = None
    recommended_by_ai: Optional[bool] = None
    notes: Optional[str] = None

class TrainingOut(TrainingCreate):
    id: int
    created_at: datetime
    employee_name: Optional[str] = None

    class Config:
        from_attributes = True

# Asset Request Schemas
class AssetRequestCreate(BaseModel):
    employee_id: str
    item_name: str
    description: Optional[str] = None
    priority: str = "Normal"

class AssetRequestUpdate(BaseModel):
    status: str
    it_response: Optional[str] = None
    reviewed_by_id: Optional[str] = None

class AssetRequestOut(BaseModel):
    id: int
    employee_id: str
    item_name: str
    description: Optional[str] = None
    priority: str
    status: str
    it_response: Optional[str] = None
    reviewed_by_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    employee_name: Optional[str] = None
    reviewed_by_name: Optional[str] = None

    class Config:
        from_attributes = True

# Onboarding Invitation Schemas
class OnboardingInvitationOut(BaseModel):
    id: int
    employee_id: str
    employee_name: Optional[str] = None
    email: str
    invitation_token: str
    expires_at: datetime
    used: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Dashboard Stats Schemas
class DashboardStatsOut(BaseModel):
    total_employees: int
    total_managers: int
    total_hrs: int
    pending_onboardings: int
    active_leaves: int
    timesheets_pending: int

# Announcement Schemas
class AnnouncementBase(BaseModel):
    title: str
    content: str
    category: str

class AnnouncementCreate(AnnouncementBase):
    pass

class AnnouncementOut(AnnouncementBase):
    id: int
    created_at: date

    class Config:
        from_attributes = True

# Onboarding Verification and Completion Schemas
class OnboardingVerifyOut(BaseModel):
    employee_id: str
    full_name: str
    email: str
    role: str
    department: str
    permissions: Optional[List[str]] = None

class OnboardingCompleteIn(BaseModel):
    token: str
    password: str

# Resource schemas
class ResourceBase(BaseModel):
    name: str
    asset_id: str
    serial_number: Optional[str] = None
    specifications: Optional[str] = None
    employee_id: Optional[str] = None
    status: str = "Available"

class ResourceCreate(ResourceBase):
    pass

class ResourceUpdate(BaseModel):
    name: Optional[str] = None
    asset_id: Optional[str] = None
    serial_number: Optional[str] = None
    specifications: Optional[str] = None
    employee_id: Optional[str] = None
    status: Optional[str] = None

class ResourceOut(ResourceBase):
    id: int
    employee_name: Optional[str] = None

    class Config:
        from_attributes = True

# Policy schemas
class PolicyBase(BaseModel):
    title: str
    category: str

class PolicyOut(PolicyBase):
    id: int
    url: str
    published_at: date

    class Config:
        from_attributes = True


# OKR / Appraisal schemas
class OKRBase(BaseModel):
    type: str
    objective: str
    key_results: Any
    progress: Optional[float] = None
    year: int
    quarter: int
    due_date: Optional[date] = None
    success_criteria: Optional[str] = None
    assigned_by: Optional[str] = None

class OKRCreate(OKRBase):
    employee_id: str

class OKRUpdate(BaseModel):
    progress: Optional[float] = None
    evidence_url: Optional[str] = None
    completion_remarks: Optional[str] = None
    appraisal_submitted: Optional[bool] = None
    appraisal_summary: Optional[str] = None
    appraisal_evidence: Optional[str] = None
    previous_ctc: Optional[Decimal] = None
    current_ctc: Optional[Decimal] = None
    appraisal_percentage: Optional[Decimal] = None

class OKROut(OKRBase):
    id: int
    employee_id: str
    evidence_url: Optional[str] = None
    completion_remarks: Optional[str] = None
    appraisal_submitted: Optional[bool] = None
    appraisal_summary: Optional[str] = None
    appraisal_evidence: Optional[str] = None
    previous_ctc: Optional[Decimal] = None
    current_ctc: Optional[Decimal] = None
    appraisal_percentage: Optional[Decimal] = None
    employee_name: Optional[str] = None

    class Config:
        from_attributes = True
