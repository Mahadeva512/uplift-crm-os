# backend/backend/app/main.py

from __future__ import annotations

import logging
import os
from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ---- Optional settings loader (won't crash if missing fields) ----
try:
    # If you have app/core/config.py with a Pydantic Settings class, keep using it.
    from app.core.config import settings  # type: ignore
except Exception:  # pragma: no cover
    settings = None  # Fallback to env only

# ---- Create app ---------------------------------------------------
app = FastAPI(title="Uplift CRM Backend", version="1.0.0")
log = logging.getLogger("uvicorn")
logging.basicConfig(level=logging.INFO)

# ---- CORS ---------------------------------------------------------
# Base allowed origins for dev + common local cases
_allowed_origins: List[str] = [
    "http://localhost",
    "http://localhost:5173",
    "http://localhost:4173",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:4173",
]

# Add typical LAN IP dev hosts (4173 is your current preview port)
lan_hosts = [
    "http://192.168.29.70:5173",
    "http://192.168.29.70:4173",
]
_allowed_origins.extend(lan_hosts)

# Pull additional frontends from env/settings without exploding if absent
env_frontend = os.getenv("FRONTEND_BASE_URL", "").strip()
if env_frontend:
    _allowed_origins.append(env_frontend)

# Some teams expose a second variable (keep both just in case)
env_frontend_alt = os.getenv("VITE_FRONTEND_BASE_URL", "").strip()
if env_frontend_alt and env_frontend_alt not in _allowed_origins:
    _allowed_origins.append(env_frontend_alt)

# If a Settings object exists and has FRONTEND_BASE_URL, add it
if settings is not None:
    fb = getattr(settings, "FRONTEND_BASE_URL", None)
    if fb and fb not in _allowed_origins:
        _allowed_origins.append(fb)

# De-duplicate while preserving order
seen = set()
origins = []
for o in _allowed_origins:
    if o and o not in seen:
        origins.append(o)
        seen.add(o)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

log.warning("✅ CORS enabled for: %s", ", ".join(origins))

# ---- Router imports (import module.router to avoid __init__ surprises) ----
# Import only what actually exists in your /app/routers directory.
# If a file is temporarily absent, the import will be skipped gracefully.

def _safe_include(import_path: str, name: str = "router") -> None:
    """Import app.routers.<module>.router and include it if present."""
    try:
        module = __import__(import_path, fromlist=[name])
        router = getattr(module, name, None)
        if router is not None:
            app.include_router(router)
            log.warning("✅ Router registered: %s", import_path)
        else:
            log.warning("⚠️  No 'router' in %s (skipped)", import_path)
    except Exception as e:  # pragma: no cover
        log.warning("⚠️  Could not include %s: %s", import_path, e)

# Core auth & users
_safe_include("app.routers.auth")
_safe_include("app.routers.users")

# Company & dashboard
_safe_include("app.routers.company_profile")
_safe_include("app.routers.dashboard")

# CRM modules
_safe_include("app.routers.leads")
_safe_include("app.routers.activities")
_safe_include("app.routers.tasks")
_safe_include("app.routers.quotation")
_safe_include("app.routers.order")              # <-- FIX: file is order.py (not orders.py)
_safe_include("app.routers.activity_overview")

# Gmail & AI helpers
_safe_include("app.routers.gmail")
_safe_include("app.routers.ai_router")
_safe_include("app.routers.ai_insights")

# Google OAuth (in routers/integrations/google_auth.py)
_safe_include("app.routers.integrations.google_auth")

# ---- Health/root --------------------------------------------------
@app.get("/", tags=["health"])
def health():
    return {"status": "ok", "service": "uplift-crm-backend"}

# ---- Notes --------------------------------------------------------
# * If you later add another frontend host, set FRONTEND_BASE_URL or VITE_FRONTEND_BASE_URL
#   in your Render env vars and redeploy — no code change needed.
# * If any router file is missing, app still boots; you'll see a warning in logs.
