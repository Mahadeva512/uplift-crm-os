from datetime import datetime, timedelta, time
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.leads import Lead
from app.models.tasks import Task
from app.models.user import User
from app.routers.auth import get_current_user
from app.utils.geo import calc_distance

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
    dependencies=[Depends(get_current_user)]
)

@router.get("/myday")
def my_day_dashboard(db: Session = Depends(get_db), current_user: User = Depends(get_current_user),
                     lat: float | None = Query(default=None), lng: float | None = Query(default=None), radius_km: float = 10):
    today = datetime.utcnow().date()
    start_today, end_today = datetime.combine(today, time.min), datetime.combine(today, time.max)
    yesterday = today - timedelta(days=1)
    start_yesterday, end_yesterday = datetime.combine(yesterday, time.min), datetime.combine(yesterday, time.max)

    new_leads = db.query(Lead).filter(Lead.company_id == current_user.company_id, Lead.created_at >= start_today, Lead.created_at <= end_today).count()
    tasks_today_q = db.query(Task).filter(Task.company_id == current_user.company_id, Task.due_date >= start_today, Task.due_date <= end_today)
    tasks_today = tasks_today_q.all()
    completed = sum(1 for t in tasks_today if str(t.status) == "Done")
    pending = len(tasks_today) - completed
    yesterday_count = db.query(Task).filter(Task.company_id == current_user.company_id, Task.due_date >= start_yesterday, Task.due_date <= end_yesterday).count()
    change = 0.0 if not yesterday_count else round((len(tasks_today) - yesterday_count) / yesterday_count * 100.0, 1)

    now, soon = datetime.utcnow(), datetime.utcnow() + timedelta(hours=24)
    reminders = db.query(Task).filter(Task.company_id == current_user.company_id, Task.due_date >= now, Task.due_date <= soon, Task.status != "Done").all()
    reminders_payload = [{"task_id": t.id, "title": t.title, "lead_id": t.lead_id,
                          "due_in_hours": round((t.due_date - now).total_seconds()/3600, 1) if t.due_date else None,
                          "priority": str(t.priority)} for t in reminders]

    nearby = []
    if lat is not None and lng is not None:
        leads_geo = db.query(Lead).filter(Lead.company_id == current_user.company_id, Lead.lat.isnot(None), Lead.lng.isnot(None)).all()
        for lead in leads_geo:
            dist = calc_distance(lat, lng, lead.lat, lead.lng)
            if dist is not None and dist <= radius_km:
                count = db.query(Task).filter(Task.company_id == current_user.company_id, Task.lead_id == lead.id, Task.status != "Done").count()
                nearby.append({"lead_id": lead.id, "lead_name": lead.name, "city": lead.city, "distance_km": dist, "open_tasks_count": count})
        nearby.sort(key=lambda x: x["distance_km"])

    return {
        "summary": {"new_leads_today": new_leads, "tasks_today": len(tasks_today), "tasks_completed": completed,
                    "tasks_pending": pending, "reminders_due": len(reminders), "nearby_leads": len(nearby)},
        "performance": {"task_change_percent_vs_yesterday": change},
        "reminders": reminders_payload, "nearby_leads": nearby
    }
