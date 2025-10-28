from pydantic import BaseModel, Field
from typing import Optional, Any, Dict
from datetime import datetime
from uuid import UUID


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------
class ActivityBase(BaseModel):
    lead_id: UUID
    type: str
    title: str
    description: Optional[str] = None
    status: str = "Pending"
    due_date: Optional[datetime] = None
    outcome: Optional[str] = None
    next_task: Optional[str] = None
    next_task_date: Optional[datetime] = None
    priority: str = "Medium"
    assigned_to: Optional[UUID] = None
    source_channel: Optional[str] = None
    auto_generated: bool = False
    parent_activity_id: Optional[UUID] = None
    meta: Dict[str, Any] = {}
    created_by: Optional[UUID] = None
    call_duration: Optional[int] = None
    geo_lat: Optional[float] = None
    geo_long: Optional[float] = None

    class Config:
        orm_mode = True


# ---------------------------------------------------------------------------
# Create / Update / Verify
# ---------------------------------------------------------------------------
class ActivityCreate(ActivityBase):
    pass


class ActivityUpdate(BaseModel):
    status: Optional[str] = None
    outcome: Optional[str] = None
    next_task: Optional[str] = None
    next_task_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    meta: Optional[Dict[str, Any]] = None


class ActivityVerify(BaseModel):
    activity_id: UUID
    verified_event: bool = True
    verification_type: Optional[str] = None
    call_duration: Optional[int] = None
    gps_verified: Optional[bool] = None
    geo_lat: Optional[float] = None
    geo_long: Optional[float] = None
    device_id: Optional[str] = None


# ---------------------------------------------------------------------------
# Minimal nested schemas for relationships
# ---------------------------------------------------------------------------
class LeadOutMini(BaseModel):
    id: UUID
    business_name: Optional[str] = None
    contact_person: Optional[str] = None

    class Config:
        orm_mode = True


class UserOutMini(BaseModel):
    id: UUID
    full_name: Optional[str] = None
    email: Optional[str] = None

    class Config:
        orm_mode = True


# ---------------------------------------------------------------------------
# Output (Extended for frontend)
# ---------------------------------------------------------------------------
class ActivityOut(ActivityBase):
    id: UUID
    completed_at: Optional[datetime] = None
    created_by: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    verified_event: Optional[bool] = None
    verification_type: Optional[str] = None
    call_duration: Optional[int] = None
    gps_verified: Optional[bool] = None
    trust_score_impact: Optional[int] = 0
    device_id: Optional[str] = None

    # ✅ Display helpers (mapped correctly)
    when: Optional[datetime] = Field(None, alias="due_date")  # pulls from due_date automatically
    lead: Optional["LeadOutMini"] = None                      # shows business_name/contact_person
    assigned_to: Optional[UUID] = None                        # plain UUID (for now)

    class Config:
        orm_mode = True
        populate_by_name = True  # enables alias field mapping
