"""
CEO Dashboard - Mos-GSM
Main FastAPI application.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import get_settings
from app.database import init_db


settings = get_settings()


class UTF8Middleware(BaseHTTPMiddleware):
    """Ensure all JSON responses have charset=utf-8."""
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type and "charset" not in content_type:
            response.headers["content-type"] = "application/json; charset=utf-8"
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown events."""
    init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    lifespan=lifespan,
)

# UTF-8 for all JSON responses
app.add_middleware(UTF8Middleware)

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
