from sqlalchemy import Column, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from app.models.base_model import TimestampMixin
from sqlalchemy.dialects.postgresql import UUID  # ✅ added
import uuid


class Lead(Base, TimestampMixin):
    __tablename__ = "leads"

    # ✅ changed from String → UUID
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    business_name = Column(String, nullable=False)  # Business Name
    contact_person = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)

    # NEW address fields
    country = Column(String, nullable=True)
    state = Column(String, nullable=True)
    city = Column(String, nullable=True)
    pincode = Column(String, nullable=True)

    stage = Column(String, default="New")
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)

    # NEW source
    lead_source = Column(String, nullable=True)

    # 🗓️ Action tracking
    next_action = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)

    # 🔒 Multi-tenant linkage
    company_id = Column(UUID(as_uuid=True), ForeignKey("company_profile.id", ondelete="CASCADE"), nullable=False)

    # 👤 Optional tracking (who created it)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # 🔗 Relationships
    company = relationship("CompanyProfile", back_populates="leads", lazy="joined")

    quotations = relationship(
        "Quotation",
        back_populates="lead",
        cascade="all, delete-orphan"
    )
    orders = relationship(
        "Order",
        back_populates="lead",
        cascade="all, delete-orphan"
    )
    tasks = relationship(
        "Task",
        back_populates="lead",
        cascade="all, delete-orphan"
    )
    # ✅ Injected fix
    activities = relationship(
        "Activity",
        back_populates="lead",
        cascade="all, delete-orphan"
    )