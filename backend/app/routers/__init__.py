"""
API Routers Package for SIH26162.
"""
from app.routers.thermal_events import router as thermal_events_router
from app.routers.facilities import router as facilities_router
from app.routers.ai import router as ai_router
from app.routers.risk import router as risk_router
from app.routers.satellite import router as satellite_router
from app.routers.alerts import router as alerts_router
from app.routers.analytics import router as analytics_router
from app.routers.reports import router as reports_router

__all__ = [
    "thermal_events_router",
    "facilities_router",
    "ai_router",
    "risk_router",
    "satellite_router",
    "alerts_router",
    "analytics_router",
    "reports_router",
]
