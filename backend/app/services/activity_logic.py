from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from uuid import UUID
from ..models.activities import Activity

FOLLOW_UP_OUTCOMES = {"Follow-Up Needed", "No Answer", "Busy"}
INTERESTED_OUTCOMES = {"Interested"}
CLOSED_OUTCOMES = {"Closed Won", "Closed Lost"}

def maybe_create_next_task(db: Session, completed_activity: Activity):
    """
    Creates the 'next task' based on outcome, links parent_activity_id to the completed one.
    """
    if completed_activity.outcome in FOLLOW_UP_OUTCOMES:
        title = "Follow-Up Call"
        due = datetime.utcnow() + timedelta(days=1)
        _spawn(db, completed_activity, title, due)

    elif completed_activity.outcome in INTERESTED_OUTCOMES and completed_activity.type in {"Call","WhatsApp","Email","Visit"}:
        title = "Send Proposal"
        due = datetime.utcnow() + timedelta(hours=4)
        _spawn(db, completed_activity, title, due, priority="Medium")

    # If closed, no auto task
    return

def _spawn(db: Session, parent: Activity, title: str, due, priority="High"):
    nxt = Activity(
        lead_id=parent.lead_id,
        type="Task",
        title=f"{title} — {parent.title}",
        description=f"Auto-created from activity {str(parent.id)} with outcome '{parent.outcome}'.",
        status="Pending",
        due_date=due,
        priority=priority,
        assigned_to=parent.assigned_to or parent.created_by,
        created_by=parent.created_by,
        auto_generated=True,
        parent_activity_id=parent.id,
        source_channel="AutoTask",
        meta={"auto_note": "System generated next task"}
    )
    db.add(nxt)
    db.flush()
    return nxt
