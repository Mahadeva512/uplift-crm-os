from app.db.session import Base, engine
from app.models import *
print("🛠 Creating all tables in PostgreSQL database...")
Base.metadata.create_all(bind=engine)
print("✅ Tables created successfully.")
