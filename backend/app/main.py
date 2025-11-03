from __future__ import annotations

import logging
import os
from typing import List
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Optional settings import (non-blocking)
try:
    from app.core.config import settings  # type: ignore
except Exception:
    settings = None

# ---------------------------------------------------------
#   App Initialization
# ---------------------------------------------------------
app = FastAPI(title="Uplift CRM Backend", version="1.0.0")
log = logging.getLogger("uvicorn")
logging.basicConfig(level=logging.INFO)

# ---------------------------------------------------------
#   CORS Configuration
# ---------------------------------------------------------
_allowed_origins: List[str] = [
    "http://localhost",
    "http://localhost:5173",
    "http://localhost:4173",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:4173",
    "http://192.168.29.70:5173",
    "http://192.168.29.70:4173",
]

env_frontend = os.getenv("FRONTEND_BASE_URL", "").strip()
if env_frontend:
    _allowed_origins.append(env_frontend)

env_frontend_alt = os.getenv("VITE_FRONTEND_BASE_URL", "").strip()
if env_frontend_alt and env_frontend_alt not in _allowed_origins:
    _allowed_origins.append(env_frontend_alt)

if settings is not None:
    fb = getattr(settings, "FRONTEND_BASE_URL", None)
    if fb and fb not in _allowed_origins:
        _allowed_origins.append(fb)

seen, origins = set(), []
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

# ---------------------------------------------------------
#   Router Registration (safe, circular-free)
# ---------------------------------------------------------
from app.routers import api_router  # <- uses your new circular-safe __init__.py
app.include_router(api_router)
log.warning("✅ All routers registered through api_router")

# ---------------------------------------------------------
#   Health Check
# ---------------------------------------------------------
@app.get("/", tags=["health"])
def health():
    return {"status": "ok", "service": "uplift-crm-backend"}
