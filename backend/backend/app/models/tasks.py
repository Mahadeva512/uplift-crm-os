from sqlalchemy import Column, String, DateTime, Float, Enum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum
from app.models.base_model import TimestampMixin
from app.db.base_class import Base
from sqlalchemy.dialects.postgresql import UUID


class TaskStatus(str, enum.Enum):
    planned = "Planned"
    in_progress = "In Progress"
    done = "Done"
    rescheduled = "Rescheduled"


class TaskPriority(str, enum.Enum):
    low = "Low"
    normal = "Normal"
    high = "High"


class Task(Base, TimestampMixin):
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)

    # 🔐 Company scoping (align with CompanyProfile table everywhere)
    company_id = Column(UUID(as_uuid=True), ForeignKey("company_profile.id", ondelete="CASCADE"), nullable=False)

    # 👤 Ownership (your routers read & set this)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=False)

    # Assignment
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Details
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)

    status = Column(Enum(TaskStatus), default=TaskStatus.planned, nullable=False)
    priority = Column(Enum(TaskPriority), default=TaskPriority.normal, nullable=False)

    due_date = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Geo helpers
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    distance_km = Column(Float, nullable=True)

    # Relationships
    lead = relationship("Lead", back_populates="tasks", lazy="joined")
    assigned_user = relationship("User", foreign_keys=[assigned_to], lazy="joined")
    creator_user = relationship("User", foreign_keys=[created_by], lazy="joined")
    company = relationship("CompanyProfile", lazy="joined")
