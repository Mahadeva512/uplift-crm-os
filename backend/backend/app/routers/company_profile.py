# app/routers/company_profile.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.session import get_db
from app.models.company_profile import CompanyProfile
from app.models.user import User
from app.routers.auth import get_current_user

router = APIRouter(
    prefix="/company",
    tags=["Company Profile"],
    dependencies=[Depends(get_current_user)],
)

# ✅ 1️⃣ Fetch current company profile (used for dashboard preload)
@router.get("/profile")
def get_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = (
        db.query(CompanyProfile)
        .filter(CompanyProfile.id == current_user.company_id)
        .first()
    )
    if not profile:
        raise HTTPException(status_code=404, detail="Company profile not found")
    return profile


# ✅ 2️⃣ Update company profile (used by onboarding modal)
@router.post("/update")
def update_company_profile(
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Updates or inserts company details for the currently authenticated user.
    Supports name, industry, team size, theme colors, etc.
    Called automatically when onboarding modal submits.
    """
    company = (
        db.query(CompanyProfile)
        .filter(CompanyProfile.id == current_user.company_id)
        .first()
    )

    if not company:
        # Auto-create if somehow missing
        company = CompanyProfile(id=current_user.company_id)
        db.add(company)

    # Allowed editable fields (security-safe)
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


# ✅ 3️⃣ Upsert fallback (legacy-compatible for your older code)
@router.post("/profile")
def upsert_profile(
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Legacy route kept for backward compatibility with existing pages.
    Internally behaves the same as /update.
    """
    company = (
        db.query(CompanyProfile)
        .filter(CompanyProfile.id == current_user.company_id)
        .first()
    )

    if not company:
        company = CompanyProfile(id=current_user.company_id, **data)
        company.created_at = datetime.utcnow()
        company.updated_at = datetime.utcnow()
        db.add(company)
    else:
        for k, v in data.items():
            setattr(company, k, v)
        company.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(company)
    return company
