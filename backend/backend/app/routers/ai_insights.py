from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

from app.db.session import get_db
from app.models.activities import Activity  # uses your existing model

# If you have a Task model, we’ll try to import it safely.
try:
    from app.models.tasks import Task  # optional, won’t crash if missing
except Exception:  # pragma: no cover
    Task = None

router = APIRouter(prefix="/ai", tags=["AI Copilot"])


# ---------------------------
# Helpers
# ---------------------------
def _now_utc() -> datetime:
    return datetime.utcnow()


def _safe_sentiment(a: Activity) -> str:
    """Read sentiment from column if present, else from meta, else Neutral."""
    try:
        if getattr(a, "ai_sentiment", None):
            return a.ai_sentiment or "Neutral"
    except Exception:
        pass

    try:
        m = a.meta or {}
        s = (m.get("ai_sentiment") or m.get("sentiment") or m.get("ai", {}).get("sentiment"))
        return s or "Neutral"
    except Exception:
        return "Neutral"


def _has_ai_suggestion(a: Activity) -> bool:
    try:
        if getattr(a, "ai_suggestion", None):
            return bool(a.ai_suggestion)
    except Exception:
        pass
    try:
        return bool((a.meta or {}).get("ai_suggestion"))
    except Exception:
        return False


def _fmt_activity(a: Activity) -> Dict[str, Any]:
    return {
        "id": str(a.id),
        "lead_id": str(a.lead_id) if getattr(a, "lead_id", None) else None,
        "type": a.type,
        "title": a.title,
        "status": a.status,
        "due_date": a.due_date.isoformat() if getattr(a, "due_date", None) else None,
        "created_at": a.created_at.isoformat() if getattr(a, "created_at", None) else None,
        "assigned_to": str(a.assigned_to) if getattr(a, "assigned_to", None) else None,
        "created_by": str(a.created_by) if getattr(a, "created_by", None) else None,
        "ai_sentiment": _safe_sentiment(a),
        "has_ai_suggestion": _has_ai_suggestion(a),
    }


# ---------------------------
# 1) Unified Insights feed (dashboard backend)
# ---------------------------
@router.get("/insights")
def ai_insights_dashboard(
    days: int = Query(7, ge=1, le=90, description="Lookback window in days"),
    lead_id: Optional[str] = Query(None, description="Filter by lead UUID"),
    user_id: Optional[str] = Query(None, description="Filter by created_by or assigned_to UUID"),
    db: Session = Depends(get_db),
):
    """
    Returns a compact analytics payload for the dashboard:
    - totals, by_status, by_type
    - sentiment distribution
    - recent AI suggestions count
    - top pending / overdue activities
    - simple user performance (created_by / assigned_to counts)
    - (optional) tasks snapshot if Task model exists
    """
    since = _now_utc() - timedelta(days=days)

    # ---- Base query (activities) ----
    q = db.query(Activity).filter(Activity.created_at >= since)

    if lead_id:
        try:
            q = q.filter(Activity.lead_id == lead_id)
        except Exception:
            pass

    if user_id:
        try:
            q = q.filter(
                (Activity.created_by == user_id) | (Activity.assigned_to == user_id)
            )
        except Exception:
            pass

    activities: List[Activity] = q.order_by(Activity.created_at.desc()).all()

    # ---- Counters ----
    total = len(activities)
    by_status: Dict[str, int] = {}
    by_type: Dict[str, int] = {}
    sentiment: Dict[str, int] = {"Positive": 0, "Neutral": 0, "Negative": 0}
    with_ai_suggestion = 0

    # For lists
    pending_list: List[Dict[str, Any]] = []
    overdue_list: List[Dict[str, Any]] = []
    recent_ai_suggestions: List[Dict[str, Any]] = []

    now = _now_utc()

    for a in activities:
        # status/type buckets
        by_status[a.status] = by_status.get(a.status, 0) + 1
        by_type[a.type] = by_type.get(a.type, 0) + 1

        # sentiment buckets
        s = _safe_sentiment(a)
        if s not in sentiment:
            sentiment[s] = 0
        sentiment[s] += 1

        # AI suggestion
        if _has_ai_suggestion(a):
            with_ai_suggestion += 1
            recent_ai_suggestions.append(_fmt_activity(a))

        # pending & overdue lists
        if a.status not in ("Completed", "Cancelled"):
            pending_list.append(_fmt_activity(a))
            if getattr(a, "due_date", None) and a.due_date < now:
                overdue_list.append(_fmt_activity(a))

    # ---- User performance (IDs only; you can join names in UI) ----
    created_by_stats: Dict[str, int] = {}
    assigned_to_stats: Dict[str, int] = {}
    for a in activities:
        if getattr(a, "created_by", None):
            k = str(a.created_by)
            created_by_stats[k] = created_by_stats.get(k, 0) + 1
        if getattr(a, "assigned_to", None):
            k = str(a.assigned_to)
            assigned_to_stats[k] = assigned_to_stats.get(k, 0) + 1

    # ---- Tasks snapshot (if Task model exists) ----
    tasks_summary = None
    if Task is not None:
        try:
            tq = db.query(Task)
            if lead_id and hasattr(Task, "lead_id"):
                tq = tq.filter(Task.lead_id == lead_id)
            if user_id:
                # try common fields
                if hasattr(Task, "assigned_to"):
                    tq = tq.filter(Task.assigned_to == user_id)
                elif hasattr(Task, "created_by"):
                    tq = tq.filter(Task.created_by == user_id)

            # basic aggregates (safe across schemas)
            tasks = tq.all()
            t_total = len(tasks)
            t_by_status: Dict[str, int] = {}
            t_overdue: int = 0
            for t in tasks:
                st = getattr(t, "status", "Unknown")
                t_by_status[st] = t_by_status.get(st, 0) + 1
                dd = getattr(t, "due_date", None)
                st_complete = str(st).lower() in ("done", "completed", "closed")
                if dd and dd < now and not st_complete:
                    t_overdue += 1

            tasks_summary = {
                "total": t_total,
                "by_status": t_by_status,
                "overdue": t_overdue,
            }
        except Exception:
            # keep insights working even if Task model not present/varies
            tasks_summary = None

    # ---- Compose response ----
    response = {
        "window_days": days,
        "filters": {"lead_id": lead_id, "user_id": user_id},
        "totals": {
            "activities": total,
            "with_ai_suggestion": with_ai_suggestion,
            "pending": by_status.get("Pending", 0) + by_status.get("Open", 0),
            "completed": by_status.get("Completed", 0),
            "overdue": len(overdue_list),
        },
        "by_status": by_status,
        "by_type": by_type,
        "sentiment": sentiment,  # Positive / Neutral / Negative
        "lists": {
            "recent_ai_suggestions": recent_ai_suggestions[:20],  # cap for UI
            "pending": pending_list[:50],
            "overdue": overdue_list[:50],
        },
        "users": {
            "created_by": created_by_stats,
            "assigned_to": assigned_to_stats,
        },
        "tasks": tasks_summary,  # None if Task model not available
        "generated_at": _now_utc().isoformat(),
    }

    return response
