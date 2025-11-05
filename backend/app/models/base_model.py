# backend/app/models/base_model.py

from sqlalchemy import Column, DateTime
from datetime import datetime
from app.db.base_class import Base  # ✅ link to global declarative Base

# ✅ Shared timestamp mixin for created/updated columns
class TimestampMixin:
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ✅ Export Base explicitly so main.py can create tables
__all__ = ["Base", "TimestampMixin"]
