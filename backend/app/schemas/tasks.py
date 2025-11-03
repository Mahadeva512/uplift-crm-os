from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID
from enum import Enum


# ==========================================================
# 🔹 ENUMS
# ==========================================================
class TaskStatus(str, Enum):
    pending = "Pending"
    in_progress = "In Progress"
    completed = "Completed"
    done = "Done"


class TaskPriority(str, Enum):
    low = "Low"
    medium = "Medium"
    high = "High"


# ==========================================================
# 🔹 BASE SCHEMA
# ==========================================================
class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    when: Optional[datetime] = None  # due date / reminder
    status: Optional[TaskStatus] = TaskStatus.pending
    priority: Optional[TaskPriority] = TaskPriority.medium
    outcome: Optional[str] = None
    assigned_to: Optional[UUID] = None
    lead_id: Optional[UUID] = None
    source_channel: Optional[str] = None
    auto_generated: Optional[bool] = False
    parent_activity_id: Optional[UUID] = None

    from pydantic import BaseModel

class MyModel(BaseModel):
    # your fields...

    class Config:
        orm_mode = True




# ==========================================================
# 🔹 CREATE / UPDATE
# ==========================================================
class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    when: Optional[datetime] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    outcome: Optional[str] = None
    assigned_to: Optional[UUID] = None
    source_channel: Optional[str] = None
    auto_generated: Optional[bool] = None
    parent_activity_id: Optional[UUID] = None


# ==========================================================
# 🔹 OUTPUT SCHEMA
# ==========================================================
class TaskOut(TaskBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
