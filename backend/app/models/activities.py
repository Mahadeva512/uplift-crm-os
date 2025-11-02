from sqlalchemy import (
    Column, String, Text, Boolean, DateTime, Integer, ForeignKey, Float, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.db.base_class import Base


class Activity(Base):
    __tablename__ = "activities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)

    # 🔗 Company isolation — align with Task/CompanyProfile
    company_id = Column(UUID(as_uuid=True), ForeignKey("company_profile.id", ondelete="CASCADE"), nullable=False)

    # Core activity details
    type = Column(String(40), nullable=False)            # Call | WhatsApp | Email | Visit | Task | Proposal ...
    title = Column(String(200), nullable=False)
    description = Column(Text)

    status = Column(String(20), nullable=False, default="Pending")
    due_date = Column(DateTime)
    completed_at = Column(DateTime)
    outcome = Column(String(60))
    next_task = Column(String(200))
    next_task_date = Column(DateTime)
    priority = Column(String(10), default="Medium")

    # Assignment & ownership
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Verification & device metadata
    verified_event = Column(Boolean, default=False)
    verification_type = Column(String(30))               # manual | call_log | gps | api | smtp
    call_duration = Column(Integer)                      # seconds
    device_id = Column(String(120))
    geo_lat = Column(Float)
    geo_long = Column(Float)
    gps_verified = Column(Boolean, default=False)

    # Chaining / automation flags
    parent_activity_id = Column(UUID(as_uuid=True), ForeignKey("activities.id", ondelete="CASCADE"), nullable=True)
    auto_generated = Column(Boolean, default=False)

    # Analytics / meta
    trust_score_impact = Column(Integer, default=0)
    source_channel = Column(String(60))                  # Google Form | Referral | Manual | ...
    meta = Column(JSONB, default=dict)

    # Relationships
    parent_activity = relationship("Activity", remote_side=[id], uselist=False)
    lead = relationship("Lead", back_populates="activities", lazy="joined")
    assigned_user = relationship("User", foreign_keys=[assigned_to], lazy="joined")
    creator_user = relationship("User", foreign_keys=[created_by], lazy="joined")
    company = relationship("CompanyProfile", lazy="joined")

    # Helpful indexes
    __table_args__ = (
        Index("ix_activities_lead_status_due", "lead_id", "status", "due_date"),
        Index("ix_activities_assignee_due", "assigned_to", "due_date"),
        Index("ix_activities_created_at", "created_at"),
        Index("ix_activities_company_id", "company_id"),
    )
