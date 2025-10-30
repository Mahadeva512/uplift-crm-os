# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
import logging
from app.db.session import Base, engine
from app import models

# ---------------------------------------------------------------------------
# 1️⃣  Create App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Uplift CRM vPro API",
    version="1.0.0",
    description="Backend API for Uplift CRM vPro with full JWT Authentication and Multi-Tenant architecture.",
    swagger_ui_parameters={"persistAuthorization": True},
)

# ---------------------------------------------------------------------------
# 2️⃣  Apply CORS Middleware
# ---------------------------------------------------------------------------
origins = [
    "http://localhost",
    "http://localhost:5173",
    "http://localhost:4173",   # ✅ your dev frontend
    "http://192.168.29.70:4173",  # ✅ LAN frontend
    "https://uplift-crm-backend.onrender.com",
    "https://uplift-crm-ui.onrender.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

logging.warning("✅ CORS middleware loaded (localhost + LAN + Render enabled)")

# ---------------------------------------------------------------------------
# 3️⃣  Import Routers
# ---------------------------------------------------------------------------
from app.routers import (
    auth,
    leads,
    tasks,
    quotation,
    order,
    dashboard,
    company_profile,
    users,
    activities,
    activity_overview,
    ai_router,
    ai_insights,
)
from app.routers.integrations import google_auth, gmail_integration
from app.routers import ai_gmail  # ✅ AI Gmail Summarize + Suggest Router

# ---------------------------------------------------------------------------
# 4️⃣  Database Init
# ---------------------------------------------------------------------------
logging.warning("🔄 Syncing database tables…")
Base.metadata.create_all(bind=engine)
logging.warning("✅ Tables ready!")

# ---------------------------------------------------------------------------
# 5️⃣  Custom OpenAPI (JWT BearerAuth in Docs)
# ---------------------------------------------------------------------------
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    schema.setdefault("components", {}).setdefault("securitySchemes", {})
    schema["components"]["securitySchemes"]["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "Paste JWT from /auth/login.",
    }
    schema["security"] = [{"BearerAuth": []}]
    app.openapi_schema = schema
    return schema

app.openapi_schema = None
app.openapi = custom_openapi
logging.warning("✅ OpenAPI BearerAuth configured")

# ---------------------------------------------------------------------------
# 6️⃣  Register Routers
# ---------------------------------------------------------------------------
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(company_profile.router)
app.include_router(leads.router)
app.include_router(tasks.router)
app.include_router(activities.router)
app.include_router(activity_overview.router)
app.include_router(quotation.router)
app.include_router(order.router)
app.include_router(dashboard.router)
app.include_router(google_auth.router)
app.include_router(gmail_integration.router)
app.include_router(ai_router.router)
app.include_router(ai_insights.router)
app.include_router(ai_gmail.router)

logging.warning("✅ Routers registered successfully")

# ---------------------------------------------------------------------------
# 7️⃣  Health Check
# ---------------------------------------------------------------------------
@app.get("/")
def root():
    return {"message": "🚀 Uplift CRM vPro backend is running on Render!"}

# ---------------------------------------------------------------------------
# 8️⃣  Run Server (for local dev)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",  # allows both localhost & LAN (192.168.x.x)
        port=8000,
        reload=True,
        log_level="info",
    )
