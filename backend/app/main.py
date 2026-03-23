"""
CEO Dashboard - Mos-GSM
Main FastAPI application.
"""
import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import get_settings
from app.database import init_db


settings = get_settings()

SYNC_INTERVAL_SEC = 15 * 60  # 15 minutes
_sync_timer = None

# Paths that don't require auth
PUBLIC_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}


class UTF8Middleware(BaseHTTPMiddleware):
    """Ensure all JSON responses have charset=utf-8."""
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type and "charset" not in content_type:
            response.headers["content-type"] = "application/json; charset=utf-8"
        return response


class AuthMiddleware(BaseHTTPMiddleware):
    """Bearer token authentication for /api/* endpoints.
    If API_TOKEN env var is empty — auth is disabled (open access).
    """
    async def dispatch(self, request: Request, call_next):
        token = settings.API_TOKEN
        if not token:
            # No token configured — skip auth
            return await call_next(request)

        path = request.url.path
        # Only protect /api/* paths. Everything else (frontend, health, docs) is public
        if not path.startswith("/api/"):
            return await call_next(request)

        # Skip auth for CORS preflight
        if request.method == "OPTIONS":
            return await call_next(request)

        # Check Authorization header
        auth = request.headers.get("authorization", "")
        if auth == f"Bearer {token}":
            return await call_next(request)

        # Check ?token= query parameter (for browser testing)
        query_token = request.query_params.get("token", "")
        if query_token == token:
            return await call_next(request)

        return JSONResponse(
            status_code=401,
            content={"detail": "Invalid or missing API token"},
        )


def _run_scheduled_sync():
    """Background sync task — runs in a separate thread."""
    global _sync_timer
    try:
        from app.services.sync import run_full_sync
        print("[SCHEDULER] Auto-sync started...")
        result = run_full_sync(days_back=7)
        print(f"[SCHEDULER] Auto-sync finished: {result}")
    except Exception as e:
        print(f"[SCHEDULER] Auto-sync error: {e}")
    finally:
        # Schedule next run
        _sync_timer = threading.Timer(SYNC_INTERVAL_SEC, _run_scheduled_sync)
        _sync_timer.daemon = True
        _sync_timer.start()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown events."""
    global _sync_timer
    init_db()

    # Start background sync after 60 sec delay (let server warm up)
    _sync_timer = threading.Timer(60, _run_scheduled_sync)
    _sync_timer.daemon = True
    _sync_timer.start()
    print(f"[SCHEDULER] Auto-sync scheduled every {SYNC_INTERVAL_SEC // 60} min (first run in 60 sec)")

    yield

    # Cleanup on shutdown
    if _sync_timer:
        _sync_timer.cancel()


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    lifespan=lifespan,
)

# UTF-8 for all JSON responses
app.add_middleware(UTF8Middleware)

# API token auth (only active if API_TOKEN is set in env)
app.add_middleware(AuthMiddleware)

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "https://ceo-dashboard-production-c36b.up.railway.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Health check ---
@app.get("/health")
async def health():
    return {"status": "ok", "app": settings.APP_NAME}


# --- Import routers ---
from app.routers import pulse, funnel, people, admin, sync

app.include_router(pulse.router, prefix="/api", tags=["Pulse"])
app.include_router(funnel.router, prefix="/api", tags=["Funnel"])
app.include_router(people.router, prefix="/api", tags=["People"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(sync.router, prefix="/api", tags=["Sync"])


# --- Serve React frontend (built static files) ---
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "dist")

if os.path.isdir(FRONTEND_DIR):
    # Serve static assets (JS, CSS, images)
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")), name="static")

    # Catch-all: serve index.html for any non-API route (SPA routing)
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = os.path.join(FRONTEND_DIR, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
