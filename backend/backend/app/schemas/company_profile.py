# app/schemas/company_profile.py
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

# -------------------------------------------------------------------
# Base schema used internally
# -------------------------------------------------------------------
class CompanyProfileBase(BaseModel):
    company_name: Optional[str] = Field(None, example="Mahadeva's Company")
    industry: Optional[str] = Field(None, example="Retail / Manufacturing / Services")
    team_size: Optional[int] = Field(None, example=10)
    theme_color: Optional[str] = Field(None, example="#0C1428")
    accent_color: Optional[str] = Field(None, example="#FACC15")
    footer_note: Optional[str] = Field(None, example="Powered by Uplift CRM OS")

# -------------------------------------------------------------------
# ✅ 1️⃣ Used for frontend update (onboarding modal)
# -------------------------------------------------------------------
class CompanyUpdate(CompanyProfileBase):
    """Fields that can be updated by user from dashboard onboarding modal"""
    pass

# -------------------------------------------------------------------
# ✅ 2️⃣ Response object used in /company/profile
# -------------------------------------------------------------------
class CompanyProfileResponse(CompanyProfileBase):
    id: Optional[str]
    email: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True  # allows SQLAlchemy → Pydantic conversion

# -------------------------------------------------------------------
# ✅ 3️⃣ Optional create schema for internal use (if needed later)
# -------------------------------------------------------------------
class CompanyProfileCreate(CompanyProfileBase):
    email: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
