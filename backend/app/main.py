import os
import sys

# Ensure backend directory is in sys.path so 'app.*' imports work from project root (e.g. on Vercel)
_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.init_db import init_db
from app.core.database import SessionLocal
from app.core.seed import seed_demo_thermal_events
from app.api.auth import router as auth_router
from app.routers.thermal_events import router as thermal_events_router
from app.routers.facilities import router as facilities_router
from app.routers.ai import router as ai_router
from app.routers.risk import router as risk_router
from app.routers.satellite import router as satellite_router
from app.routers.firms import router as firms_router
from app.routers.alerts import router as alerts_router
from app.routers.analytics import router as analytics_router
from app.routers.reports import router as reports_router
from app.routers.operator_teams import router as operator_teams_router
from app.routers.devices import router as devices_router

from contextlib import asynccontextmanager
from app.services.firms_service import get_firms_service

# Initialize database schema safely on application import/startup
init_db()

# Auto-seed demo thermal events and facilities on startup
try:
    with SessionLocal() as db_session:
        seed_demo_thermal_events(db_session, force=False)
except Exception as e:
    import logging
    logging.getLogger("main").warning(f"Could not auto-seed demo data on startup: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Startup: Safe validation and launch single resilient background FIRMS worker
    import logging
    logger = logging.getLogger("main")
    firms_svc = get_firms_service()
    if firms_svc.is_configured:
        logger.info("NASA FIRMS API key: CONFIGURED")
    else:
        logger.warning("NASA FIRMS API key: NOT CONFIGURED")
    firms_svc.start_background_worker()
    yield
    # 2. Shutdown: Gracefully stop background worker
    firms_svc.stop_background_worker()


app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API for SIH26162 - THERMOSAFE AI Industrial Thermal Intelligence",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS Middleware
# Allows explicit domains in settings.CORS_ORIGINS as well as standard cloud deployments and local dev.
# When allow_credentials=True, browsers reject wildcard "*", so we filter "*" and allow regex/explicit list.
_raw_origins = settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else [settings.CORS_ORIGINS]
_cors_origins = [o.rstrip("/") for o in _raw_origins if o and o != "*"]
for _allowed_origin in [
    "https://thermosafe-ai-2.onrender.com",
    "https://thermosafe-ai.onrender.com",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "null",
]:
    if _allowed_origin not in _cors_origins:
        _cors_origins.append(_allowed_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|.*\.vercel\.app|.*\.onrender\.com|.*\.railway\.app|.*\.netlify\.app|.*\.pages\.dev)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Mount API Routers
app.include_router(auth_router, prefix=settings.API_PREFIX)
app.include_router(thermal_events_router, prefix=settings.API_PREFIX)
app.include_router(facilities_router, prefix=settings.API_PREFIX)
app.include_router(ai_router, prefix=settings.API_PREFIX)
app.include_router(risk_router, prefix=settings.API_PREFIX)
app.include_router(satellite_router, prefix=settings.API_PREFIX)
app.include_router(firms_router, prefix=settings.API_PREFIX)
app.include_router(alerts_router, prefix=settings.API_PREFIX)
app.include_router(analytics_router, prefix=settings.API_PREFIX)
app.include_router(reports_router, prefix=settings.API_PREFIX)
app.include_router(operator_teams_router, prefix=settings.API_PREFIX)
app.include_router(devices_router, prefix=settings.API_PREFIX)


@app.get("/health", tags=["Health"])
async def health_root():
    """
    Lightweight root health check endpoint to verify backend service reachability.
    Does not require NASA FIRMS or database connectivity.
    """
    return {
        "status": "ok"
    }


@app.get("/api/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint returning service status, timestamp, and FIRMS configuration state.
    Safe against internal exceptions; never exposes secrets.
    """
    from datetime import datetime, timezone
    now_iso = datetime.now(timezone.utc).isoformat()
    res = {
        "status": "ok",
        "service": "thermosafe-ai",
        "firmsConfigured": False,
        "timestamp": now_iso
    }
    try:
        firms = get_firms_service()
        res["firmsConfigured"] = bool(firms.is_configured)
        res["firms"] = firms.get_health_status()
    except Exception as exc:
        res["firmsConfigured"] = False
        res["firms"] = {
            "firms_configured": False,
            "status": "UNAVAILABLE",
            "last_error": str(exc)
        }
    return res


@app.get("/api/firms/status", tags=["Satellite Telemetry (NASA FIRMS)"])
async def firms_status():
    """
    Safe internal status endpoint reporting FIRMS configuration,
    worker health, and cached event metrics. Never returns the MAP_KEY.
    """
    svc = get_firms_service()
    h = svc.get_health_status()
    return {
        "configured": h["firms_configured"],
        "worker_running": h["firms_worker_running"],
        "source": svc.preferred_sensor,
        "last_attempt": h["last_attempt"],
        "last_successful_fetch": h["last_successful_fetch"],
        "last_error": h["last_error"],
        "cached_event_count": h["cached_event_count"],
        "stale_age_seconds": h["stale_age_seconds"],
        "next_refresh": h["next_scheduled_fetch"],
        "status": h["status"]
    }


# Locate frontend static assets for unified single-domain deployment
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_CANDIDATE_FRONTEND_DIRS = [
    os.path.join(_BASE_DIR, "frontend"),
    _BASE_DIR,
    os.path.join(os.getcwd(), "frontend"),
    os.getcwd(),
]
FRONTEND_DIR = None
for _dir in _CANDIDATE_FRONTEND_DIRS:
    if os.path.exists(_dir) and os.path.exists(os.path.join(_dir, "index.html")):
        FRONTEND_DIR = _dir
        break


@app.get("/config.js", include_in_schema=False)
async def get_config_js():
    if FRONTEND_DIR:
        cfg = os.path.join(FRONTEND_DIR, "config.js")
        if os.path.exists(cfg):
            return FileResponse(cfg, media_type="application/javascript")
    return Response(content="window.__THERMOSAFE_API_URL__ = window.__THERMOSAFE_API_URL__ || '';", media_type="application/javascript")


@app.get("/firebase-messaging-sw.js", include_in_schema=False)
async def get_firebase_sw():
    if FRONTEND_DIR:
        sw = os.path.join(FRONTEND_DIR, "firebase-messaging-sw.js")
        if os.path.exists(sw):
            return FileResponse(sw, media_type="application/javascript")
    return Response(content="// SW fallback", media_type="application/javascript")


@app.get("/", tags=["Root"])
async def root(request: Request):
    """
    Root endpoint: Serves the ThermoSafe AI SPA if HTML is requested in a browser;
    otherwise returns service status and links to docs and health.
    """
    accept = request.headers.get("accept", "")
    if FRONTEND_DIR and ("text/html" in accept or "*/*" in accept):
        index_path = os.path.join(FRONTEND_DIR, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path, media_type="text/html")

    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "status": "running",
        "docs": "/docs",
        "health": "/api/health"
    }


@app.get("/index.html", include_in_schema=False)
async def get_index_html(request: Request):
    return await root(request)

