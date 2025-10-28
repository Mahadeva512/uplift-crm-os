from sqlalchemy import Column, String, Float, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.db.base_class import Base
from app.models.base_model import TimestampMixin


class Quotation(Base, TimestampMixin):
    """
    Represents a quotation linked to a specific Lead.
    Each quotation can have multiple Orders generated from it.
    """

    __tablename__ = "quotations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)

    # Core quotation details
    item_name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    rate = Column(Float, nullable=False, default=0.0)
    total = Column(Float, nullable=False, default=0.0)

    # Lifecycle + remarks
    status = Column(String, default="Draft")  # Draft / Sent / Approved / Rejected
    remarks = Column(String, nullable=True)

    # Relationships
    lead = relationship("Lead", back_populates="quotations")
    orders = relationship(
        "Order",
        back_populates="quotation",
        cascade="all, delete-orphan"
    )

    # Optional future extensions for Phase 7.3+ (themeable PDFs)
    template_style = Column(String, default="classic")  # classic / modern / gst
    footer_note = Column(String, nullable=True)  # e.g. "Thank you for your business!"

    def __repr__(self):
        return f"<Quotation(id='{self.id}', lead_id='{self.lead_id}', total={self.total})>"
