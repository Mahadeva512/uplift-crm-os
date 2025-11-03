# ============================================================
#  UPLIFT CRM BACKEND ROUTER REGISTRATION (CIRCULAR-SAFE)
# ============================================================

from fastapi import APIRouter

# Import each router directly
from app.routers import (
    auth,
    users,
    leads,
    tasks,
    activities,
    quotations,
    orders,
)

# Create the master API router
api_router = APIRouter()

# Register individual routers (prefix + tag)
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(leads.router, prefix="/leads", tags=["Leads"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])
api_router.include_router(activities.router, prefix="/activities", tags=["Activities"])
api_router.include_router(quotations.router, prefix="/quotations", tags=["Quotations"])
api_router.include_router(orders.router, prefix="/orders", tags=["Orders"])
