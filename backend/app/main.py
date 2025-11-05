# backend/app/main.py
import logging, os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.db.session import engine
from app.models import base_model as base

# ---------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("uplift-crm")
logger.info("🚀 Starting Uplift CRM Backend...")

# ---------------------------------------------------------------------
# App Lifecycle
# ---------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🔌 Startup")
    yield
    logger.info("🛑 Shutdown")

app = FastAPI(
    title="Uplift CRM OS",
    description="Uplift CRM unified backend (production)",
    version="1.0.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------
env_origins = os.getenv("CORS_ORIGINS", "")
ALLOWED_ORIGINS = [x.strip() for x in env_origins.split(",") if x.strip()] or [
    "https://uplift-crm-ui.onrender.com",
    "https://uplift-crm-os.onrender.com",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
logger.info(f"🌐 Allowed CORS Origins: {ALLOWED_ORIGINS}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=86400,
)

# ---------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------
from app.routers import (
    activities,
    activity_overview,
    ai_gmail,
    ai_insights,
    ai_router,
    auth,
    company_profile,
    dashboard,
    gmail,
    leads,
    order,
    quotation,
    tasks,
    users,
)
from app.routers.integrations import google_auth

routers = [
    (activities.router, "/activities"),
    (activity_overview.router, "/activity_overview"),
    (ai_gmail.router, "/ai_gmail"),
    (ai_insights.router, "/ai"),
    (ai_router.router, "/ai_router"),
    (auth.router, "/auth"),
    (google_auth.router, "/auth"),
    (company_profile.router, "/company"),
    (dashboard.router, "/dashboard"),
    (gmail.router, "/gmail"),
    (leads.router, "/leads"),
    (order.router, "/order"),
    (quotation.router, "/quotation"),
    (tasks.router, "/tasks"),
    (users.router, "/users"),
]

for router, prefix in routers:
    app.include_router(router, prefix=prefix)
    logger.info(f"✅ Router mounted: {prefix}")

# ---------------------------------------------------------------------
# Root & Health
# ---------------------------------------------------------------------
@app.get("/")
def root():
    return {
        "status": "ok",
        "app": "Uplift CRM OS",
        "backend": os.getenv("BACKEND_BASE_URL"),
        "frontend": os.getenv("FRONTEND_BASE_URL"),
    }

@app.get("/health")
def health():
    return {"status": "healthy", "service": "Uplift CRM OS"}

# ---------------------------------------------------------------------
# Database Init
# ---------------------------------------------------------------------
try:
    base.Base.metadata.create_all(bind=engine)
    logger.info("📦 Database tables ensured successfully.")
except Exception as e:
    logger.warning(f"⚠️ Table creation skipped: {e}")
