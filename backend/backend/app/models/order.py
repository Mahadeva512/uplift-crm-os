from sqlalchemy import Column, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.db.base_class import Base
from app.models.base_model import TimestampMixin


class Order(Base, TimestampMixin):
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quotation_id = Column(UUID(as_uuid=True), ForeignKey("quotations.id", ondelete="SET NULL"), nullable=True)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)

    total_value = Column(Float, nullable=False)
    status = Column(String, default="Pending")  # Pending / Processing / Completed / Cancelled
    remarks = Column(String, nullable=True)

    # Relationships
    quotation = relationship("Quotation", back_populates="orders")
    lead = relationship("Lead", back_populates="orders")

