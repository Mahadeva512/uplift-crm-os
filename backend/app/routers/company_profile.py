# backend/app/routers/company_profile.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.session import get_db
from app.models.company_profile import CompanyProfile
from app.models.user import User
from app.routers.auth import get_current_user

# ✅ Removed prefix="/company" to prevent /company/company duplication
router = APIRouter(tags=["Company Profile"])


# ---------------------------------------------------------------------
# 1️⃣ Fetch current company profile — Auto-create if missing
# ---------------------------------------------------------------------
@router.get("/profile")
def get_company_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns the current company profile for the logged-in user.
    Auto-creates a blank profile if none exists to prevent 500/404 errors.
    """
    if not getattr(current_user, "company_id", None):
        new_company = CompanyProfile(
            company_name=f"{current_user.full_name.split()[0]}'s Company"
            if getattr(current_user, "full_name", None)
            else "My Company",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(new_company)
        db.commit()
        db.refresh(new_company)
        current_user.company_id = new_company.id
        db.commit()
        return new_company

    company = (
        db.query(CompanyProfile)
        .filter(CompanyProfile.id == current_user.company_id)
        .first()
    )
    if not company:
        company = CompanyProfile(
            id=current_user.company_id,
            company_name="My Company",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(company)
        db.commit()
        db.refresh(company)
    return company


# ---------------------------------------------------------------------
# 2️⃣ Update company profile — used by Onboarding modal
# ---------------------------------------------------------------------
@router.post("/update")
def update_company_profile(
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Updates or creates company details.
    Fields allowed: company_name, industry, team_size, theme_color, accent_color, footer_note.
    """
    company = (
        db.query(CompanyProfile)
        .filter(CompanyProfile.id == current_user.company_id)
        .first()
    )

    if not company:
        company = CompanyProfile(
            id=current_user.company_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(company)
        db.commit()
        db.refresh(company)

    allowed_fields = {
        "company_name",
        "industry",
        "team_size",
        "theme_color",
        "accent_color",
        "footer_note",
    }

    for key, value in data.items():
        if key in allowed_fields and value not in [None, ""]:
            setattr(company, key, value)

    company.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(company)
    return company


# ---------------------------------------------------------------------
# 3️⃣ Backward compatibility (legacy support)
# ---------------------------------------------------------------------
@router.post("/profile", include_in_schema=False)
def upsert_profile(
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Legacy alias for /update — kept for backward compatibility."""
    return update_company_profile(data, db, current_user)
