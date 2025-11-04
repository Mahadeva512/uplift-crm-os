from .session import engine, get_db
from .base_class import Base
from . import base  # ✅ ensures app.db.base is available for main.py import
