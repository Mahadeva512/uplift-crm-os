from sqlalchemy.orm import Session
from app.db.session import engine
from app.models.company_profile import CompanyProfile
from app.models.user import User
from app.models.leads import Lead
import uuid
from datetime import datetime

print("🌱 Starting database seeding...")

session = Session(bind=engine)

# 1️⃣ Create company
company = CompanyProfile(
    id=uuid.uuid4(),
    company_name="Uplift Business Growth Solutions",
    theme_color="#0048E8",
    accent_color="#FACC15",
    footer_note="Empower Growth. Inspire Change."
)
session.add(company)
session.commit()
print(f"✅ Company created: {company.company_name}")

# 2️⃣ Create admin user
user = User(
    id=uuid.uuid4(),
    full_name="Admin User",
    email="admin@uplift.com",
    hashed_password="dummyhashedpassword",
    role="admin",
    company_id=company.id,
    is_active=True
)
session.add(user)
session.commit()
print(f"✅ User created: {user.email}")

# 3️⃣ Create one lead
lead = Lead(
    id=uuid.uuid4(),
    business_name="Royal Look Salon",
    contact_person="Karthik R",
    email="royallook@example.com",
    phone="9876543210",
    city="Mysuru",
    state="Karnataka",
    country="India",
    pincode="570001",
    stage="New Lead",
    lat=12.2958,
    lng=76.6394,
    company_id=company.id,
    created_by=user.id,
    created_at=datetime.utcnow(),
    updated_at=datetime.utcnow(),
    is_active=True
)
session.add(lead)
session.commit()
print(f"✅ Lead created: {lead.business_name}")

session.close()
print("🌿 Seeding completed successfully!")
