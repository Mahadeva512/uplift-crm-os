from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime
from io import BytesIO

from app.db.session import get_db
from app.models.quotation import Quotation
from app.models.leads import Lead
from app.models.company_profile import CompanyProfile
from app.models.user import User
from app.routers.auth import get_current_user
from app.utils.pdf_generator import build_quotation_pdf, default_company_profile

router = APIRouter(
    prefix="/quotations",
    tags=["Quotations"],
    dependencies=[Depends(get_current_user)]
)

# GET – all (company scoped)
@router.get("/")
def get_all_quotations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Quotation).filter(Quotation.company_id == current_user.company_id).all()

# POST – create
@router.post("/", status_code=status.HTTP_201_CREATED)
def create_quotation(data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    lead = db.query(Lead).filter(Lead.id == data.get("lead_id"), Lead.company_id == current_user.company_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    total = float(data["quantity"]) * float(data["rate"])
    quotation = Quotation(**data, total=total)
    quotation.company_id = current_user.company_id
    quotation.created_by = current_user.id

    db.add(quotation)
    db.commit()
    db.refresh(quotation)
    return quotation

# PUT – update
@router.put("/{quotation_id}")
def update_quotation(quotation_id: str, data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    quotation = db.query(Quotation).filter(Quotation.id == quotation_id, Quotation.company_id == current_user.company_id).first()
    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")

    if "lead_id" in data and data["lead_id"] != quotation.lead_id:
        lead = db.query(Lead).filter(Lead.id == data["lead_id"], Lead.company_id == current_user.company_id).first()
        if not lead:
            raise HTTPException(status_code=400, detail="Invalid lead for this company")

    for k, v in data.items():
        setattr(quotation, k, v)

    quotation.total = float(quotation.quantity) * float(quotation.rate)
    quotation.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(quotation)
    return quotation

# DELETE – delete
@router.delete("/{quotation_id}")
def delete_quotation(quotation_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    quotation = db.query(Quotation).filter(Quotation.id == quotation_id, Quotation.company_id == current_user.company_id).first()
    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")

    db.delete(quotation)
    db.commit()
    return {"message": "Quotation deleted successfully"}

# GET – download PDF
@router.get("/{quotation_id}/pdf")
def download_quotation_pdf(quotation_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    quotation = db.query(Quotation).filter(Quotation.id == quotation_id, Quotation.company_id == current_user.company_id).first()
    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")

    lead = db.query(Lead).filter(Lead.id == quotation.lead_id, Lead.company_id == current_user.company_id).first()
    company = db.query(CompanyProfile).filter(CompanyProfile.id == current_user.company_id).first() or default_company_profile()

    pdf_bytes = build_quotation_pdf(quotation, lead, company)
    filename = f"Quotation_{quotation.id}.pdf"

    return StreamingResponse(BytesIO(pdf_bytes), media_type="application/pdf", headers={
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Content-Type": "application/octet-stream",
    })
