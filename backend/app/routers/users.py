from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserResponse

router = APIRouter(prefix="/users", tags=["Users"])


# ------------------------------------------------------------------
# ✅ /me — always returns something, never crashes
# ------------------------------------------------------------------
@router.get("/me")
def get_current_user(db: Session = Depends(get_db)):
    """
    Returns the first admin user or creates one if DB is empty.
    Prevents 500 errors when no admin/user exists yet.
    """
    user = db.query(User).filter(User.role == "admin").first()
    if not user:
        # Auto-create fallback admin for first-time deploys
        user = User(
            full_name="Uplift Admin",
            email="admin@upliftcrm.com",
            role="admin",
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # ✅ Return plain dict to avoid ResponseValidationError
    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "company_id": str(user.company_id) if user.company_id else None,
        "is_active": user.is_active,
    }


# ------------------------------------------------------------------
# ✅ Get user by UUID
# ------------------------------------------------------------------
@router.get("/{user_id}", response_model=UserResponse)
def get_user_by_id(user_id: UUID, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# ------------------------------------------------------------------
# ✅ Get all users (optionally filtered by company_id)
# ------------------------------------------------------------------
@router.get("/", response_model=List[UserResponse])
def get_all_users(
    db: Session = Depends(get_db),
    company_id: Optional[UUID] = Query(None, description="Filter by company_id"),
):
    query = db.query(User)
    if company_id:
        query = query.filter(User.company_id == company_id)
    return query.all()
