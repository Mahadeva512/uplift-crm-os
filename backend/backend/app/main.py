import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.routers import (
    auth,
    users,
    leads,
    tasks,
    activities,
    order,
)
from app.core.config import settings

log = logging.getLogger("uvicorn.error")

app = FastAPI(
    title="Uplift CRM Backend",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ----------------------------------------------------
# ✅ CORS CONFIGURATION
# ----------------------------------------------------
_default_frontends = [
    "http://localhost:4173",
    "http://127.0.0.1:4173",
    "http://192.168.29.70:4173",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://192.168.29.70:5173",
    "https://uplift-crm-frontend.onrender.com",
]

# Include Render Frontend if provided via ENV
if settings.FRONTEND_BASE_URL and settings.FRONTEND_BASE_URL not in _default_frontends:
    _default_frontends.append(settings.FRONTEND_BASE_URL)

# Apply CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=_default_frontends,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# ----------------------------------------------------
# ✅ ENSURE CORS HEADERS (Safety Net Middleware)
# ----------------------------------------------------
class EnsureCorsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
        except Exception:
            log.exception("Unhandled error in request")
            response = JSONResponse({"detail": "Internal Server Error"}, status_code=500)

        origin = request.headers.get("origin", "")
        if origin in _default_frontends:
            response.headers.setdefault("Access-Control-Allow-Origin", origin)
            response.headers.setdefault("Access-Control-Allow-Credentials", "true")
            response.headers.setdefault("Vary", "Origin")
        return response

app.add_middleware(EnsureCorsMiddleware)

# ----------------------------------------------------
# ✅ HEALTH & TEST ENDPOINTS
# ----------------------------------------------------
@app.get("/")
def root():
    return {"status": "ok", "message": "Uplift CRM Backend running 🚀"}

@app.head("/")
def root_head():
    return JSONResponse(status_code=200, content={"ok": True})

@app.options("/")
def root_options():
    return JSONResponse(status_code=200, content={"ok": True})

# ----------------------------------------------------
# ✅ ROUTER REGISTRATIONS
# ----------------------------------------------------
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(leads.router, prefix="/leads", tags=["Leads"])
app.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])
app.include_router(activities.router, prefix="/activities", tags=["Activities"])
app.include_router(orders.router, prefix="/orders", tags=["Orders"])

# ----------------------------------------------------
# ✅ STARTUP EVENT
# ----------------------------------------------------
@app.on_event("startup")
async def startup_event():
    log.warning("✅ Uplift Backend Ready with CORS and Health Routes")
