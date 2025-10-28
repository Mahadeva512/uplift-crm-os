from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID
from datetime import datetime


# ==========================================================
# 🔹 BASE
# ==========================================================
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

    class Config:
        from_attributes = True  # ✅ (Pydantic v2 compatible)


# ==========================================================
# 🔹 CREATE / LOGIN
# ==========================================================
class UserCreate(UserBase):
    password: str
    company_name: Optional[str] = None  # for auto-company creation


class UserLogin(BaseModel):
    email: EmailStr
    password: str


# ==========================================================
# 🔹 RESPONSE (for all user-related API returns)
# ==========================================================
class UserResponse(UserBase):
    id: UUID
    company_id: Optional[UUID] = None
    role: Optional[str] = "user"
    is_active: Optional[bool] = True
    last_login: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # 👇 Optional company info (helpful in dashboards / Copilot)
    company_name: Optional[str] = None
    theme_color: Optional[str] = None
    accent_color: Optional[str] = None

    class Config:
        from_attributes = True  # replaces orm_mode=True in Pydantic v2


# ==========================================================
# 🔹 SHORT VERSION (for embedding in activities/tasks)
# ==========================================================
class UserMini(BaseModel):
    id: UUID
    full_name: Optional[str] = None
    role: Optional[str] = None
    email: Optional[EmailStr] = None

    class Config:
        from_attributes = True
