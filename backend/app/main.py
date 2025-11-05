import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.db.session import engine
from app.models import base_model as base  # ✅ correct declarative base import

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
        # Future startup logic (e.g., caching, background tasks, etc.)
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
logger.info(f"🌐 Allowed CORS Origins: {settings.CORS_ORIGINS}")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
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

router_list = [
    (activities.router, "/activities"),
    (activity_overview.router, "/activity_overview"),
    (ai_gmail.router, "/ai_gmail"),
    (ai_insights.router, "/ai_insights"),
    (ai_router.router, "/ai_router"),
    (auth.router, "/auth"),
    (company_profile.router, "/company"),
    (dashboard.router, "/dashboard"),
    (gmail.router, "/gmail"),
    (leads.router, "/leads"),
    (order.router, "/order"),
    (quotation.router, "/quotation"),
    (tasks.router, "/tasks"),
    (users.router, "/users"),
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
        "backend_base_url": settings.BACKEND_BASE_URL,
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
# ✅ Future Notes
# ---------------------------------------------------------------------
# - Just drop new routers into app/routers and append them above.
# - Logging auto-streams to Render logs.
# - CORS automatically syncs with config.
# - Safe for async DB and background services.
