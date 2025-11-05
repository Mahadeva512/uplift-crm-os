import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from contextlib import asynccontextmanager
from app.db.session import engine
import app.db.base as base  # ✅ directly import base module
from app.utils.logger import log_setup

# ✅ Setup Logging
logger = log_setup()
logger.info("🚀 Starting Uplift CRM Backend...")

# ✅ Lifespan Event
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🔌 Application startup...")
    try:
        # Any startup logic can go here
        yield
    finally:
        logger.info("🛑 Application shutdown...")

# ✅ Initialize App
app = FastAPI(
    title="Uplift CRM OS",
    description="Unified CRM OS Backend - Production Deployment",
    version="1.0.0",
    lifespan=lifespan,
)

# ✅ CORS Configuration (Render + Local)
logger.info(f"🌐 CORS origins: {settings.CORS_ORIGINS}")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Include Routers Dynamically
from app.routers import (
    auth,
    users,
    leads,
    activities,
    tasks,
    company_profile,
    ai,
    quotations,
    orders,
    products,
)

router_list = [
    (auth.router, "/auth"),
    (users.router, "/users"),
    (leads.router, "/leads"),
    (activities.router, "/activities"),
    (tasks.router, "/tasks"),
    (company_profile.router, "/company"),
    (ai.router, "/ai"),
    (quotations.router, "/quotations"),
    (orders.router, "/orders"),
    (products.router, "/products"),
]

for r, prefix in router_list:
    app.include_router(r, prefix=prefix)
    logger.info(f"✅ Router mounted: {prefix}")

# ✅ Root Route
@app.get("/")
async def root():
    return {
        "status": "ok",
        "app": "Uplift CRM OS",
        "version": "1.0.0",
        "base_url": settings.BACKEND_BASE_URL,
    }


# ✅ Health Check Route (for Render)
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Uplift CRM OS"}


# ✅ Create Tables (optional safety in production)
try:
    base.Base.metadata.create_all(bind=engine)
    logger.info("📦 Database tables ensured.")
except Exception as e:
    logger.warning(f"⚠️ Table creation skipped: {e}")
