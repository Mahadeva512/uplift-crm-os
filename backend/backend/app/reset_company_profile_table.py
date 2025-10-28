from app.db.session import engine, Base
from app.models.company_profile import CompanyProfile

print("⚙️ Dropping 'company_profile' table if exists...")
CompanyProfile.__table__.drop(engine, checkfirst=True)
print("✅ Dropped successfully (if existed).")

print("🧱 Recreating 'company_profile' table with UUID id column...")
Base.metadata.create_all(bind=engine, tables=[CompanyProfile.__table__])
print("✅ 'company_profile' table recreated successfully.")
