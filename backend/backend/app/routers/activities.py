from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from app.db.session import get_db
from app.models.activities import Activity
from app.models.leads import Lead
from app.models.user import User
from app.schemas.activities import ActivityCreate, ActivityUpdate, ActivityOut, ActivityVerify
from app.routers.auth import get_current_user

router = APIRouter(prefix="/activities", tags=["Activities"])


def _must_own_or_admin(current_user: User, activity: Activity):
    if current_user.role == "admin":
        return
    if current_user.id not in {activity.created_by, activity.assigned_to}:
        raise HTTPException(status_code=403, detail="Not allowed")


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------
@router.post("", response_model=ActivityOut)
def create_activity(
    payload: ActivityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not payload.lead_id or not payload.type:
        raise HTTPException(status_code=400, detail="lead_id and type are required")

    lead = db.query(Lead).filter(
        Lead.id == payload.lead_id, Lead.company_id == current_user.company_id
    ).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found or not yours")

    now = datetime.utcnow()
    call_duration = None
    if (payload.type or "").lower() == "call" and payload.meta:
        start, end = payload.meta.get("call_start"), payload.meta.get("call_end")
        if start and end:
            try:
                t1, t2 = datetime.fromisoformat(start), datetime.fromisoformat(end)
                call_duration = int((t2 - t1).total_seconds())
            except Exception:
                pass

    activity = Activity(
        **payload.dict(exclude_unset=True, exclude={"company_id", "created_by"}),
        company_id=current_user.company_id,
        created_by=current_user.id,
        assigned_to=payload.assigned_to or current_user.id,
        created_at=now,
        call_duration=call_duration,
    )

    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


# ---------------------------------------------------------------------------
# LIST  (joined Lead + User)
# ---------------------------------------------------------------------------
@router.get("", response_model=List[ActivityOut])
def list_activities(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    lead_id: Optional[UUID] = None,
    status: Optional[str] = None,
    type: Optional[str] = None,
    verified: Optional[bool] = None,
    assigned_to: Optional[UUID] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    limit: int = Query(200, le=500),
    offset: int = 0,
):
    q = (
        db.query(Activity)
        .options(joinedload(Activity.lead), joinedload(Activity.assigned_user))
        .filter(Activity.company_id == current_user.company_id)
    )

    if current_user.role != "admin":
        q = q.filter(or_(Activity.assigned_to == current_user.id, Activity.created_by == current_user.id))
    if lead_id:
        q = q.filter(Activity.lead_id == lead_id)
    if status:
        q = q.filter(Activity.status == status)
    if type:
        q = q.filter(Activity.type == type)
    if verified is not None:
        q = q.filter(Activity.verified_event == verified)
    if assigned_to:
        if current_user.role == "admin" or assigned_to == current_user.id:
            q = q.filter(Activity.assigned_to == assigned_to)
    if date_from:
        q = q.filter(Activity.created_at >= date_from)
    if date_to:
        q = q.filter(Activity.created_at <= date_to)

    data = q.order_by(Activity.created_at.desc()).offset(offset).limit(limit).all()
    # --- serialize with lead/assignee names + unified when ---
    return [
        {
            **a.__dict__,
            "lead_name": getattr(a.lead, "name", None),
            "assigned_to_name": getattr(a.assigned_user, "full_name", None),
            "when": a.due_date or getattr(a, "activity_date", None),
        }
        for a in data
    ]


# ---------------------------------------------------------------------------
# GET / UPDATE / VERIFY / DELETE
# ---------------------------------------------------------------------------
@router.get("/{activity_id}", response_model=ActivityOut)
def get_activity(activity_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    act = (
        db.query(Activity)
        .options(joinedload(Activity.lead), joinedload(Activity.assigned_user))
        .filter(Activity.id == activity_id, Activity.company_id == current_user.company_id)
        .first()
    )
    if not act:
        raise HTTPException(404, "Activity not found")
    _must_own_or_admin(current_user, act)
    return {
        **act.__dict__,
        "lead_name": getattr(act.lead, "name", None),
        "assigned_to_name": getattr(act.assigned_user, "full_name", None),
    }


@router.put("/{activity_id}", response_model=ActivityOut)
def update_activity(activity_id: UUID, payload: ActivityUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    act = db.query(Activity).filter(Activity.id == activity_id, Activity.company_id == current_user.company_id).first()
    if not act:
        raise HTTPException(404, "Activity not found")
    _must_own_or_admin(current_user, act)

    protected = {"id", "company_id", "created_by", "created_at"}
    for k, v in payload.dict(exclude_unset=True).items():
        if k not in protected:
            setattr(act, k, v)

    if payload.status == "Completed" and not act.completed_at:
        act.completed_at = datetime.utcnow()

    db.commit()
    db.refresh(act)
    return act


@router.post("/verify", response_model=ActivityOut)
def verify_activity(payload: ActivityVerify, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    act = db.query(Activity).filter(Activity.id == payload.activity_id, Activity.company_id == current_user.company_id).first()
    if not act:
        raise HTTPException(404, "Activity not found")
    _must_own_or_admin(current_user, act)
    for k, v in payload.dict(exclude={"activity_id"}).items():
        if v is not None and k not in {"company_id", "created_by", "created_at"}:
            setattr(act, k, v)
    db.commit()
    db.refresh(act)
    return act


@router.delete("/{activity_id}")
def delete_activity(activity_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    act = db.query(Activity).filter(Activity.id == activity_id, Activity.company_id == current_user.company_id).first()
    if not act:
        raise HTTPException(404, "Activity not found")
    _must_own_or_admin(current_user, act)
    db.delete(act)
    db.commit()
    return {"ok": True}


# ---------------------------------------------------------------------------
# SUMMARY  (unchanged)
# ---------------------------------------------------------------------------
@router.get("/summary/overview")
def summary_overview(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    q = db.query(Activity).filter(Activity.company_id == current_user.company_id)
    if current_user.role != "admin":
        q = q.filter(or_(Activity.assigned_to == current_user.id, Activity.created_by == current_user.id))

    total = q.count()
    verified = q.filter(Activity.verified_event == True).count()
    pending = q.filter(Activity.status.in_(["Planned", "Pending", "Overdue"])).count()
    completed = q.filter(Activity.status == "Completed").count()
    return {"total": total, "verified": verified, "pending": pending, "completed": completed}
