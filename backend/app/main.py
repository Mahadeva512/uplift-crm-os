# backend/app/main.py
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.db.session import engine
from app.models import base_model as base

# ---------------------------------------------------------------------
# ✅ Logging Configuration
# ---------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("uplift-crm")
logger.info("🚀 Starting Uplift CRM Backend...")

# ---------------------------------------------------------------------
# ✅ Application Lifecycle Hooks
# ---------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🔌 Application startup...")
    try:
        yield
    finally:
        logger.info("🛑 Application shutdown...")

# ---------------------------------------------------------------------
# ✅ Initialize FastAPI App
# ---------------------------------------------------------------------
app = FastAPI(
    title="Uplift CRM OS",
    description="Unified CRM OS Backend - Production Deployment",
    version="1.0.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------
# ✅ CORS Configuration (Render + Local)
# ---------------------------------------------------------------------
ALLOWED_ORIGINS = [
    "https://uplift-crm-ui.onrender.com",
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
)

# ---------------------------------------------------------------------
# ✅ Router Imports (match exact file names)
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
# ✅ Integrations folder router (Google OAuth)
from app.routers.integrations import google_auth

# ---------------------------------------------------------------------
# ✅ Router Mounts (with correct prefixes)
# ---------------------------------------------------------------------
router_list = [
    (activities.router, "/activities"),
    (activity_overview.router, "/activity_overview"),
    (ai_gmail.router, "/ai_gmail"),
    (ai_insights.router, "/ai"),          # final endpoint: /ai/insights
    (ai_router.router, "/ai_router"),
    (auth.router, "/auth"),
    (google_auth.router, "/auth"),        # final endpoint: /auth/google
    (company_profile.router, "/company"), # final: /company/profile
    (dashboard.router, "/dashboard"),
    (gmail.router, "/gmail"),
    (leads.router, "/leads"),
    (order.router, "/order"),
    (quotation.router, "/quotation"),
    (tasks.router, "/tasks"),
    (users.router, "/users"),             # final: /users/me
]

for router, prefix in router_list:
    app.include_router(router, prefix=prefix)
    logger.info(f"✅ Router mounted: {prefix}")

# ---------------------------------------------------------------------
# ✅ Root & Health Routes
# ---------------------------------------------------------------------
@app.get("/")
async def root():
    return {
        "status": "ok",
        "app": "Uplift CRM OS",
        "version": "1.0.0",
        "backend_base_url": "https://uplift-crm-os.onrender.com",
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Uplift CRM OS"}

# ---------------------------------------------------------------------
# ✅ Database Table Creation (Safety Net)
# ---------------------------------------------------------------------
try:
    base.Base.metadata.create_all(bind=engine)
    logger.info("📦 Database tables ensured successfully.")
except Exception as e:
    logger.warning(f"⚠️ Table creation skipped due to error: {e}")

# ---------------------------------------------------------------------
# ✅ Notes
# ---------------------------------------------------------------------
# - No double prefixes (all routers now clean).
# - Google OAuth (integrations/google_auth.py) mounted correctly under /auth.
# - CORS whitelist covers Render UI and local dev.
# - Safe for future routers; just add imports and append to router_list.
