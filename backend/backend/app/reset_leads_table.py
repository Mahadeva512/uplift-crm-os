# ================================
# reset_leads_table.py — FINAL FIXED VERSION
# ================================
import os
import sys
from sqlalchemy import text

# ✅ Ensure Python recognizes backend/app as package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import engine
from app.models.leads import Lead
from sqlalchemy.orm import declarative_base

Base = Lead.__bases__[0]  # Get the Base class dynamically

with engine.connect() as conn:
    print("⚙️ Dropping only 'leads' table safely (without touching dependent enums)...")
    conn.execute(text("DROP TABLE IF EXISTS leads CASCADE;"))
    conn.commit()
    print("✅ 'leads' table dropped successfully.")

print("🧱 Recreating 'leads' table with updated columns...")
Base.metadata.create_all(bind=engine, tables=[Lead.__table__])
print("✅ 'leads' table recreated successfully with business_name and other fields.")
