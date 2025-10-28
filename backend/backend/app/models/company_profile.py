from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from app.db.base_class import Base


class CompanyProfile(Base):
    __tablename__ = "company_profile"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_name = Column(String, default="Uplift Business Growth Solutions")
    logo_url = Column(String, nullable=True)
    address = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    gst_no = Column(String, nullable=True)
    theme_color = Column(String, default="#0048E8")
    accent_color = Column(String, default="#FACC15")
    footer_note = Column(String, default="Thank you for your business!")
    signature_url = Column(String, nullable=True)
    template_style = Column(String, default="classic")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 🔗 Relationship to Leads
    leads = relationship("Lead", back_populates="company", cascade="all, delete-orphan")
