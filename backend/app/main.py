"""
CEO Dashboard — Mos-GSM
Main FastAPI application.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.database import init_db


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown events."""
    # Initialize database tables
    init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    lifespan=lifespan,
)

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "https://*.up.railway.app",
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
from app.routers import pulse, funnel, people, admin

app.include_router(pulse.router, prefix="/api", tags=["Pulse"])
app.include_router(funnel.router, prefix="/api", tags=["Funnel"])
app.include_router(people.router, prefix="/api", tags=["People"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
