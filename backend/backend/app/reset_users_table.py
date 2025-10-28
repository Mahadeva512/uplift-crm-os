from app.db.session import engine, Base
from app.models.user import User

print("⚙️ Dropping 'users' table safely...")
User.__table__.drop(engine, checkfirst=True)
print("✅ Dropped successfully.")

print("🧱 Recreating 'users' table with UUID id column...")
Base.metadata.create_all(bind=engine, tables=[User.__table__])
print("✅ 'users' table recreated successfully.")
