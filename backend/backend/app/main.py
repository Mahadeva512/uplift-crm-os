import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, JSONResponse
from starlette.requests import Request

from .routers import auth, users, leads, tasks, activities, quotations, orders
from .routers.integrations import google_auth
from .routers import ai_insights, ai_router

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARNING)

BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "").rstrip("/")
FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "").rstrip("/")

# Render + local defaults
_default_frontends = {
    "http://localhost:4173",
    "http://127.0.0.1:4173",
    "http://192.168.29.70:4173",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://192.168.29.70:5173",
}
if FRONTEND_BASE_URL:
    _default_frontends.add(FRONTEND_BASE_URL)

origins = sorted(_default_frontends)

app = FastAPI(
    title="Uplift CRM vPro API",
    version="1.0.0",
)

# --- CORS must be first ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|192\.168\.\d+\.\d+)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# --- Safety net: if something raises deep in the stack, still attach CORS ---
class EnsureCorsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            resp = await call_next(request)
        except Exception as e:
            # Convert to JSON 500 but still attach CORS
            log.exception("Unhandled error")
            resp = JSONResponse({"detail": "Internal Server Error"}, status_code=500)
        # Mirror CORS for known local dev origins
        origin = request.headers.get("origin", "")
        if any(origin.startswith(o) for o in origins):
            resp.headers.setdefault("Access-Control-Allow-Origin", origin)
            resp.headers.setdefault("Vary", "Origin")
            if "credentials" in resp.headers.get("Access-Control-Allow-Credentials", "").lower() or True:
                resp.headers["Access-Control-Allow-Credentials"] = "true"
        return resp

app.add_middleware(EnsureCorsMiddleware)

# --- Routers ---
app.include_router(auth.router, prefix="", tags=["auth"])
app.include_router(google_auth.router, prefix="", tags=["google-oauth"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(leads.router, prefix="/leads", tags=["leads"])
app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
app.include_router(activities.router, prefix="/activities", tags=["activities"])
app.include_router(quotations.router, prefix="/quotations", tags=["quotations"])
app.include_router(orders.router, prefix="/orders", tags=["orders"])
app.include_router(ai_router.router, prefix="/ai", tags=["ai"])
app.include_router(ai_insights.router, prefix="/ai", tags=["ai-insights"])

@app.get("/", tags=["health"])
def health():
    return {"ok": True, "backend": BACKEND_BASE_URL or "unset"}

# Optional: HEAD/OPTIONS for health so mobile preflights don’t 405
@app.head("/", tags=["health"])
def head_health():
    return Response(status_code=200)

@app.options("/{rest_of_path:path}")
def options_catch_all(rest_of_path: str):
    return Response(status_code=200)
