from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID

# Import your existing related schemas
from app.schemas.activities import ActivityOut
from app.schemas.tasks import TaskOut  # ✅ Use only TaskOut


# ==========================================================
# 🔹 BASE SCHEMA
# ==========================================================
class LeadBase(BaseModel):
    business_name: str
    contact_person: Optional[str] = None

    # ✅ Allow blank email ("") and validate only when provided
    email: Optional[str] = None

    # Phone kept optional to avoid breaking current flows
    phone: Optional[str] = None

    # Address
    country: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    pincode: Optional[str] = None

    # Lead details
    stage: Optional[str] = "New"
    lat: Optional[float] = None
    lng: Optional[float] = None
    lead_source: Optional[str] = None
    next_action: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = True

    @validator("email", pre=True)
    def _normalize_email(cls, v):
        # Accept None or empty string from UI
        if v is None or v == "":
            return None
        # If provided, do a light sanity check (keep it lenient)
        if "@" not in v:
            raise ValueError("Invalid email format")
        return v

    class Config:
        orm_mode = True


# ==========================================================
# 🔹 CREATE / UPDATE
# ==========================================================
class LeadCreate(LeadBase):
    # Inherits the lenient email handling from LeadBase
    pass


class LeadUpdate(BaseModel):
    business_name: Optional[str] = None
    contact_person: Optional[str] = None

    # ✅ Make update lenient too (blank allowed, validate only when present)
    email: Optional[str] = None

    phone: Optional[str] = None
    country: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    pincode: Optional[str] = None
    stage: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    lead_source: Optional[str] = None
    next_action: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None

    @validator("email", pre=True)
    def _normalize_email(cls, v):
        if v is None or v == "":
            return None
        if "@" not in v:
            raise ValueError("Invalid email format")
        return v


# ==========================================================
# 🔹 COMPANY PROFILE OUT
# ==========================================================
class CompanyProfileOut(BaseModel):
    id: UUID
    company_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    theme_color: Optional[str] = None
    accent_color: Optional[str] = None
    footer_note: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


# ==========================================================
# 🔹 LEAD OUT (with relations)
# ==========================================================
class LeadOut(LeadBase):
    id: UUID
    company_id: UUID
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    company: Optional[CompanyProfileOut] = None

    # 👇 Enriched summary fields for your UI
    total_activities: Optional[int] = 0
    total_tasks: Optional[int] = 0
    last_activity_date: Optional[datetime] = None
    last_task_date: Optional[datetime] = None

    # 👇 Optional nested data (joinedload-ready)
    activities: Optional[List[ActivityOut]] = None
    tasks: Optional[List[TaskOut]] = None

    class Config:
        orm_mode = True
