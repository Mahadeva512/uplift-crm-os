# ============================================================
#  UPLIFT CRM BACKEND ROUTER REGISTRATION (CIRCULAR-SAFE)
# ============================================================

from fastapi import APIRouter

# Import routers individually — match file names exactly
from app.routers import (
    auth,
    users,
    leads,
    tasks,
    activities,
    quotation,
    order,
    dashboard,
    company_profile,
    gmail,
    ai_router,
    ai_insights,
    ai_gmail,
    activity_overview,
)

api_router = APIRouter()

# Register routers (safe, no circular imports)
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(leads.router, prefix="/leads", tags=["Leads"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])
api_router.include_router(activities.router, prefix="/activities", tags=["Activities"])
api_router.include_router(quotation.router, prefix="/quotation", tags=["Quotation"])
api_router.include_router(order.router, prefix="/order", tags=["Order"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(company_profile.router, prefix="/company", tags=["Company Profile"])
api_router.include_router(gmail.router, prefix="/gmail", tags=["Gmail"])
api_router.include_router(ai_router.router, prefix="/ai-router", tags=["AI Router"])
api_router.include_router(ai_insights.router, prefix="/ai-insights", tags=["AI Insights"])
api_router.include_router(ai_gmail.router, prefix="/ai-gmail", tags=["AI Gmail"])
api_router.include_router(activity_overview.router, prefix="/activity-overview", tags=["Activity Overview"])
