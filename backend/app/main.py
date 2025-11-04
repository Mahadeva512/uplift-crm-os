from __future__ import annotations
import importlib
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

# ---------------------------------------------------------
#   App Initialization
# ---------------------------------------------------------
app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION)
log = logging.getLogger("uvicorn")

# ---------------------------------------------------------
#   CORS Configuration (Frontend + Render)
# ---------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
log.warning(f"✅ CORS enabled for: {', '.join(settings.CORS_ORIGINS)}")

# ---------------------------------------------------------
#   Dynamic Router Mounting
# ---------------------------------------------------------
def mount_router(path: str, prefix: str = "", tag: str = ""):
    try:
        module = importlib.import_module(path)
        router = getattr(module, "router", None)
        if router:
            app.include_router(router, prefix=prefix, tags=[tag] if tag else None)
            log.warning(f"✅ Router registered: {path}")
        else:
            log.warning(f"⚠️  No router found in {path}")
    except Exception as e:
        log.warning(f"⚠️  Could not include {path}: {e}")

# Core routers
mount_router("app.routers.auth", prefix="/auth", tag="auth")
mount_router("app.routers.users", prefix="/users", tag="users")
mount_router("app.routers.company_profile", prefix="/company", tag="company")
mount_router("app.routers.dashboard", prefix="/dashboard", tag="dashboard")
mount_router("app.routers.leads", prefix="/leads", tag="leads")
mount_router("app.routers.activities", prefix="/activities", tag="activities")
mount_router("app.routers.tasks", prefix="/tasks", tag="tasks")
mount_router("app.routers.quotation", prefix="/quotation", tag="quotation")
mount_router("app.routers.order", prefix="/order", tag="order")
mount_router("app.routers.activity_overview", prefix="/activity_overview", tag="activity")
mount_router("app.routers.gmail", prefix="/gmail", tag="gmail")
mount_router("app.routers.ai_router", prefix="/ai", tag="ai")
mount_router("app.routers.ai_insights", prefix="/ai", tag="ai_insights")

# ---------------------------------------------------------
#   Injected Fix — Google OAuth router mount
# ---------------------------------------------------------
try:
    from app.routers.integrations import google_auth
    app.include_router(google_auth.router, prefix="/auth", tags=["Google Auth"])
    log.warning("✅ Google OAuth router mounted under /auth (for /auth/google, /auth/google/callback)")
except Exception as e:
    log.warning(f"⚠️  Could not include Google OAuth router: {e}")

# ---------------------------------------------------------
#   Health Check
# ---------------------------------------------------------
@app.get("/", tags=["health"])
def health():
    return {"status": "ok", "service": settings.PROJECT_NAME}
