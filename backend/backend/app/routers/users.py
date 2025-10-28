from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserResponse
from typing import List, Optional
from uuid import UUID  # ✅ ensures correct type parsing

router = APIRouter(prefix="/users", tags=["Users"])


# ✅ Keep /me ABOVE /{user_id} to avoid UUID parsing errors
@router.get("/me", response_model=UserResponse)
def get_current_user(db: Session = Depends(get_db)):
    """
    Temporary endpoint until JWT-based 'current_user' is wired up.
    Returns first admin record.
    """
    user = db.query(User).filter(User.role == "admin").first()
    if not user:
        raise HTTPException(status_code=404, detail="No admin found")
    return user


# ✅ Get user by ID (used in LeadCard.jsx)
@router.get("/{user_id}", response_model=UserResponse)
def get_user_by_id(user_id: UUID, db: Session = Depends(get_db)):  # str → UUID
    """
    Fetch a user's public details by UUID.
    Used by the frontend LeadCard to show 'Created By'.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# ✅ Get all users — with optional company isolation
@router.get("/", response_model=List[UserResponse])
def get_all_users(
    db: Session = Depends(get_db),
    company_id: Optional[UUID] = Query(None, description="Filter by company_id"),  # str → UUID
):
    """
    Fetch all users.
    If 'company_id' query param is provided, only return users belonging to that company.
    Example: /users?company_id=44b08f14-8219-4173-8fa0-b8320f1461a4
    """
    query = db.query(User)
    if company_id:
        query = query.filter(User.company_id == company_id)
    return query.all()
