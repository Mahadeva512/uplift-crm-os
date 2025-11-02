# create_db.py

import sys, os
sys.path.append(os.path.dirname(__file__))

# ✅ Import full app to register models
from app import models
from app.db.session import Base, engine
from sqlalchemy import inspect

print("🧱 Creating all tables in PostgreSQL (uplift database)...")

# Drop and recreate tables if you want to reset
# Base.metadata.drop_all(bind=engine)

Base.metadata.create_all(bind=engine)

print("✅ Tables created successfully!")

insp = inspect(engine)
print("📋 Tables in database:", insp.get_table_names())
