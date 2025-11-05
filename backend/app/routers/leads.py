# backend/app/routers/leads.py

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.session import get_db
from app.models.leads import Lead
from app.schemas.leads import LeadCreate, LeadUpdate, LeadOut
from app.models.user import User
from app.routers.auth import get_current_user

# ❗ No prefix here. main.py already mounts this router at "/leads"
router = APIRouter(tags=["Leads"])

# ---------------------------------------------------------------------
# ✅ CHECK DUPLICATE (must be before /{lead_id})
# ---------------------------------------------------------------------
@router.get("/check-duplicate")
def check_duplicate(
    email: Optional[str] = Query(None),
    phone: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Checks if a lead with the given email or phone already exists.
    Called as: GET /leads/check-duplicate?email=... OR ?phone=...
    """
    if not email and not phone:
        raise HTTPException(status_code=400, detail="Please provide email or phone")

    q = db.query(Lead)
    exists = None
    if email:
        exists = q.filter(Lead.email == email).first()
    elif phone:
        exists = q.filter(Lead.phone == phone).first()

    return {"exists": bool(exists)}

# ---------------------------------------------------------------------
# ✅ CREATE LEAD
# ---------------------------------------------------------------------
@router.post("/", response_model=LeadOut)
def create_lead(
    lead: LeadCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Prevent duplicate leads inside the same company
    existing = (
        db.query(Lead)
        .filter(
            Lead.company_id == current_user.company_id,
            ((Lead.phone == lead.phone) | (Lead.email == lead.email))
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail="A lead with this phone or email already exists."
        )

    new_lead = Lead(
        **lead.dict(exclude_unset=True),
        company_id=current_user.company_id,
        created_by=current_user.id,
    )
    db.add(new_lead)
    db.commit()
    db.refresh(new_lead)
    return new_lead

# ---------------------------------------------------------------------
# ✅ GET ALL LEADS
# ---------------------------------------------------------------------
@router.get("/", response_model=List[LeadOut])
def get_all_leads(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Lead)
        .filter(Lead.company_id == current_user.company_id)
        .order_by(Lead.created_at.desc())
        .all()
    )

# ---------------------------------------------------------------------
# ✅ GET LEAD BY ID
# ---------------------------------------------------------------------
@router.get("/{lead_id}", response_model=LeadOut)
def get_lead_by_id(
    lead_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lead = (
        db.query(Lead)
        .filter(Lead.id == lead_id, Lead.company_id == current_user.company_id)
        .first()
    )
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead

# ---------------------------------------------------------------------
# ✅ UPDATE LEAD
# ---------------------------------------------------------------------
@router.put("/{lead_id}", response_model=LeadOut)
def update_lead(
    lead_id: str,
    payload: LeadUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lead = (
        db.query(Lead)
        .filter(Lead.id == lead_id, Lead.company_id == current_user.company_id)
        .first()
    )
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    for key, value in payload.dict(exclude_unset=True).items():
        setattr(lead, key, value)

    db.commit()
    db.refresh(lead)
    return lead

# ---------------------------------------------------------------------
# ✅ DELETE LEAD
# ---------------------------------------------------------------------
@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lead(
    lead_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lead = (
        db.query(Lead)
        .filter(Lead.id == lead_id, Lead.company_id == current_user.company_id)
        .first()
    )
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    db.delete(lead)
    db.commit()
    return {"message": "Lead deleted successfully"}
