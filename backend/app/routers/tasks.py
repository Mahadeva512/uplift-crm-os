from datetime import datetime, timedelta
from math import radians, sin, cos, sqrt, atan2
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from uuid import UUID
from app.db.session import get_db
from app.models.tasks import Task
from app.models.leads import Lead
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.tasks import TaskBase

router = APIRouter(prefix="/tasks", tags=["Tasks"])


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------
def calc_distance(lat1, lng1, lat2, lng2):
    if not all([lat1, lng1, lat2, lng2]):
        return None
    R = 6371.0
    dlat, dlon = radians(lat2 - lat1), radians(lng2 - lng1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return round(R * 2 * atan2(sqrt(a), sqrt(1 - a)), 2)


# ---------------------------------------------------------------------------
# LIST (joined Lead + User)
# ---------------------------------------------------------------------------
@router.get("/", response_model=List[TaskBase])
def get_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    lead_id: Optional[UUID] = None,
    status: Optional[str] = None,
    limit: int = Query(200, le=500),
):
    q = (
        db.query(Task)
        .options(joinedload(Task.lead), joinedload(Task.assigned_user))
        .filter(Task.company_id == current_user.company_id)
    )
    if current_user.role != "admin":
        q = q.filter(or_(Task.assigned_to == current_user.id, Task.created_by == current_user.id))
    if lead_id:
        q = q.filter(Task.lead_id == lead_id)
    if status:
        q = q.filter(Task.status == status)

    tasks = q.order_by(Task.created_at.desc()).limit(limit).all()
    return [
        {
            **t.__dict__,
            "lead_name": getattr(t.lead, "name", None),
            "assigned_to_name": getattr(t.assigned_user, "full_name", None),
            "when": t.due_date,
        }
        for t in tasks
    ]


# ---------------------------------------------------------------------------
# CREATE / UPDATE / DELETE / SPECIAL VIEWS
# ---------------------------------------------------------------------------
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=TaskBase)
def create_task(data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    lead = db.query(Lead).filter(Lead.id == data.get("lead_id"), Lead.company_id == current_user.company_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    allowed = {"lead_id", "title", "description", "status", "due_date", "priority", "assigned_to", "lat", "lng"}
    clean = {k: v for k, v in (data or {}).items() if k in allowed}
    if not clean.get("assigned_to"):
        clean["assigned_to"] = current_user.id

    task = Task(**clean)
    task.company_id = current_user.company_id
    task.created_by = current_user.id

    last = (
        db.query(Task)
        .filter(Task.company_id == current_user.company_id, Task.lead_id == task.lead_id)
        .order_by(Task.created_at.desc())
        .first()
    )
    if last and task.lat and task.lng and last.lat and last.lng:
        task.distance_km = calc_distance(last.lat, last.lng, task.lat, task.lng)

    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.put("/{task_id}", response_model=TaskBase)
def update_task(task_id: str, data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    task = db.query(Task).filter(Task.id == task_id, Task.company_id == current_user.company_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if current_user.role != "admin" and current_user.id not in {task.assigned_to, task.created_by}:
        raise HTTPException(status_code=403, detail="Not allowed")

    protected = {"id", "company_id", "created_by", "created_at"}
    for k, v in (data or {}).items():
        if k not in protected:
            setattr(task, k, v)

    if (data or {}).get("status") == "Done":
        task.completed_at = datetime.utcnow()
    task.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}")
def delete_task(task_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    task = db.query(Task).filter(Task.id == task_id, Task.company_id == current_user.company_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if current_user.role != "admin" and current_user.id not in {task.assigned_to, task.created_by}:
        raise HTTPException(status_code=403, detail="Not allowed")
    db.delete(task)
    db.commit()
    return {"message": "Task deleted"}


# ---- Today / Upcoming / Reminders ----
@router.get("/today", response_model=List[TaskBase])
def today(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    today = datetime.utcnow().date()
    tomorrow = today + timedelta(days=1)
    q = (
        db.query(Task)
        .options(joinedload(Task.lead), joinedload(Task.assigned_user))
        .filter(Task.company_id == current_user.company_id, Task.due_date >= today, Task.due_date < tomorrow)
    )
    if current_user.role != "admin":
        q = q.filter(or_(Task.assigned_to == current_user.id, Task.created_by == current_user.id))
    data = q.order_by(Task.due_date.asc()).all()
    return [
        {
            **t.__dict__,
            "lead_name": getattr(t.lead, "name", None),
            "assigned_to_name": getattr(t.assigned_user, "full_name", None),
            "when": t.due_date,
        }
        for t in data
    ]


@router.get("/upcoming", response_model=List[TaskBase])
def upcoming(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    today = datetime.utcnow().date()
    q = (
        db.query(Task)
        .options(joinedload(Task.lead), joinedload(Task.assigned_user))
        .filter(Task.company_id == current_user.company_id, Task.due_date > today)
    )
    if current_user.role != "admin":
        q = q.filter(or_(Task.assigned_to == current_user.id, Task.created_by == current_user.id))
    data = q.order_by(Task.due_date.asc()).all()
    return [
        {
            **t.__dict__,
            "lead_name": getattr(t.lead, "name", None),
            "assigned_to_name": getattr(t.assigned_user, "full_name", None),
            "when": t.due_date,
        }
        for t in data
    ]


@router.get("/reminders/run")
def reminders(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    now = datetime.utcnow()
    soon = now + timedelta(hours=24)
    q = (
        db.query(Task)
        .options(joinedload(Task.lead))
        .filter(Task.company_id == current_user.company_id, Task.due_date <= soon, Task.due_date >= now, Task.status != "Done")
    )
    if current_user.role != "admin":
        q = q.filter(or_(Task.assigned_to == current_user.id, Task.created_by == current_user.id))
    due = q.all()
    return [
        {
            "task_id": t.id,
            "title": t.title,
            "lead_name": getattr(t.lead, "name", None),
            "due_in_hours": round((t.due_date - now).total_seconds() / 3600, 1) if t.due_date else None,
        }
        for t in due
    ]
