from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.db.base_class import Base
from app.models.base_model import TimestampMixin

class Company(Base, TimestampMixin):
    __tablename__ = "companies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    domain = Column(String, nullable=True)  # optional, for email-domain based future logic

    def __repr__(self):
        return f"<Company(id='{self.id}', name='{self.name}')>"
