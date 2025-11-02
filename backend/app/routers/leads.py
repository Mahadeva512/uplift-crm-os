from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.models.leads import Lead
from app.schemas.leads import LeadCreate, LeadUpdate, LeadOut
from app.models.user import User
from app.routers.auth import get_current_user
from typing import Optional
router = APIRouter(prefix="/leads", tags=["Leads"])


# ==========================================================
# ✅ CHECK DUPLICATE (must be before /{lead_id})
# ==========================================================

@router.get("/check-duplicate")
def check_duplicate(
    email: Optional[str] = Query(None),
    phone: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Checks if a lead with the given email or phone already exists.
    Example: /leads/check-duplicate?email=test@gmail.com
    or /leads/check-duplicate?phone=9876543210
    """
    if not email and not phone:
        raise HTTPException(status_code=400, detail="Please provide email or phone")

    query = db.query(Lead)
    if email:
        exists = query.filter(Lead.email == email).first()
    elif phone:
        exists = query.filter(Lead.phone == phone).first()
    else:
        exists = None

    return {"exists": bool(exists)}

# ==========================================================
# ✅ CREATE LEAD (Now includes duplicate detection)
# ==========================================================
@router.post("/", response_model=LeadOut)
def create_lead(
    lead: LeadCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # ✅ Prevent duplicate leads (by phone or email)
    existing_lead = (
        db.query(Lead)
        .filter(
            Lead.company_id == current_user.company_id,
            ((Lead.phone == lead.phone) | (Lead.email == lead.email))
        )
        .first()
    )
    if existing_lead:
        raise HTTPException(
            status_code=400,
            detail="A lead with this phone or email already exists."
        )

    # ✅ Create lead (unchanged logic)
    new_lead = Lead(
        business_name=lead.business_name,
        contact_person=lead.contact_person,
        email=lead.email,
        phone=lead.phone,
        country=lead.country,
        state=lead.state,
        city=lead.city,
        pincode=lead.pincode,
        stage=lead.stage,
        lat=lead.lat,
        lng=lead.lng,
        lead_source=lead.lead_source,
        next_action=lead.next_action,
        notes=lead.notes,
        is_active=lead.is_active,
        company_id=current_user.company_id,
        created_by=current_user.id,
    )

    db.add(new_lead)
    db.commit()
    db.refresh(new_lead)
    return new_lead


# ==========================================================
# ✅ GET ALL LEADS
# ==========================================================
@router.get("/", response_model=List[LeadOut])
def get_all_leads(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    leads = (
        db.query(Lead)
        .filter(Lead.company_id == current_user.company_id)
        .order_by(Lead.created_at.desc())
        .all()
    )
    return leads


# ==========================================================
# ✅ GET LEAD BY ID
# ==========================================================
@router.get("/{lead_id}", response_model=LeadOut)
def get_lead(
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


# ==========================================================
# ✅ UPDATE LEAD
# ==========================================================
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


# ==========================================================
# ✅ DELETE LEAD
# ==========================================================
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
