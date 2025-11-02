from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.db.base_class import Base
from app.models.base_model import TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="admin")  # admin | manager | exec
    is_active = Column(Boolean, default=True)

    # ✅ Fixed: company_id should also be UUID
    company_id = Column(UUID(as_uuid=True), ForeignKey("company_profile.id", ondelete="CASCADE"), nullable=False)
    company = relationship("CompanyProfile", backref="users")

    def __repr__(self):
        return f"<User(id='{self.id}', email='{self.email}', role='{self.role}')>"
