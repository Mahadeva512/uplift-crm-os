from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.order import Order
from app.models.quotation import Quotation
from app.models.leads import Lead
from app.models.user import User
from app.routers.auth import get_current_user

router = APIRouter(
    prefix="/orders",
    tags=["Orders"],
    dependencies=[Depends(get_current_user)]
)

@router.get("/")
def get_all_orders(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Order).filter(Order.company_id == current_user.company_id).all()

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_order(data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    quotation = db.query(Quotation).filter(Quotation.id == data.get("quotation_id"), Quotation.company_id == current_user.company_id).first()
    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")

    lead = db.query(Lead).filter(Lead.id == quotation.lead_id, Lead.company_id == current_user.company_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    order = Order(
        quotation_id=quotation.id,
        lead_id=lead.id,
        total_value=quotation.total,
        status="Pending",
        remarks=data.get("remarks", "")
    )
    order.company_id = current_user.company_id
    order.created_by = current_user.id

    db.add(order)
    db.commit()
    db.refresh(order)
    return order

@router.put("/{order_id}")
def update_order(order_id: str, data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    order = db.query(Order).filter(Order.id == order_id, Order.company_id == current_user.company_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if "quotation_id" in data and data["quotation_id"] != order.quotation_id:
        q = db.query(Quotation).filter(Quotation.id == data["quotation_id"], Quotation.company_id == current_user.company_id).first()
        if not q:
            raise HTTPException(status_code=400, detail="Invalid quotation for this company")

    if "lead_id" in data and data["lead_id"] != order.lead_id:
        l = db.query(Lead).filter(Lead.id == data["lead_id"], Lead.company_id == current_user.company_id).first()
        if not l:
            raise HTTPException(status_code=400, detail="Invalid lead for this company")

    for k, v in data.items():
        setattr(order, k, v)
    order.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(order)
    return order

@router.delete("/{order_id}")
def delete_order(order_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    order = db.query(Order).filter(Order.id == order_id, Order.company_id == current_user.company_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    db.delete(order)
    db.commit()
    return {"message": "Order deleted"}
