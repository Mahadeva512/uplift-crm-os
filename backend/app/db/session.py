from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.db.base_class import Base  # ✅ import the real Base used by models

# ✅ Database URL
DATABASE_URL = settings.DATABASE_URL

# ✅ Engine
engine = create_engine(DATABASE_URL, echo=True)

# ✅ Session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ✅ FastAPI dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
