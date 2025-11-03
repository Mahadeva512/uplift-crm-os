# ============================================================
#  UPLIFT CRM BACKEND ROUTER REGISTRATION (CIRCULAR-SAFE)
# ============================================================

from fastapi import APIRouter

# Import routers individually (no top-level import of app.routers)
from app.routers import (
    auth,
    users,
    leads,
    tasks,
    activities,
    quotations,
    orders,
)

api_router = APIRouter()

# Register routers with tags
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(leads.router, prefix="/leads", tags=["Leads"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])
api_router.include_router(activities.router, prefix="/activities", tags=["Activities"])
api_router.include_router(quotations.router, prefix="/quotations", tags=["Quotations"])
api_router.include_router(orders.router, prefix="/orders", tags=["Orders"])
