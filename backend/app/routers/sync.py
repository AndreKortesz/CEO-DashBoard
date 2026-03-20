"""
/api/sync — Data synchronization endpoints.
Triggers loading data from Bitrix24 and Roistat into PostgreSQL.
"""
from fastapi import APIRouter, Query
from datetime import datetime
from app.services.sync import run_full_sync, sync_leads, sync_deals, sync_visits, sync_roistat
from app.database import SessionLocal

router = APIRouter()


@router.post("/sync/run")
def trigger_full_sync(days_back: int = Query(90, ge=1, le=365)):
    """
    Run full data sync from all Phase 1 sources.
    This pulls leads, deals, visits from Bitrix24 and channels from Roistat.
    """
    started = datetime.utcnow()
    results = run_full_sync(days_back=days_back)
    results["started_at"] = started.isoformat()
    results["finished_at"] = datetime.utcnow().isoformat()
    results["duration_sec"] = round((datetime.utcnow() - started).total_seconds(), 1)
    return results


@router.post("/sync/leads")
def trigger_sync_leads(days_back: int = Query(90, ge=1, le=365)):
    """Sync only leads from Bitrix24."""
    db = SessionLocal()
    try:
        return sync_leads(db, days_back=days_back)
    finally:
        db.close()


@router.post("/sync/deals")
def trigger_sync_deals(days_back: int = Query(180, ge=1, le=365)):
    """Sync only deals from Bitrix24."""
    db = SessionLocal()
    try:
        return sync_deals(db, days_back=days_back)
    finally:
        db.close()


@router.post("/sync/visits")
def trigger_sync_visits(days_back: int = Query(180, ge=1, le=365)):
    """Sync only visits from Bitrix24."""
    db = SessionLocal()
    try:
        return sync_visits(db, days_back=days_back)
    finally:
        db.close()


@router.post("/sync/roistat")
def trigger_sync_roistat(days_back: int = Query(30, ge=1, le=365)):
    """Sync only Roistat channel data."""
    db = SessionLocal()
    try:
        return sync_roistat(db, days_back=days_back)
    finally:
        db.close()


@router.get("/sync/roistat-debug")
def debug_roistat():
    """Debug: show raw Roistat API response."""
    from app.services.roistat import roistat_service
    from app.config import get_settings
    from datetime import date, timedelta
    s = get_settings()
    try:
        raw = roistat_service._call("project/analytics/data", {
            "from": (date.today() - timedelta(days=7)).isoformat(),
            "to": date.today().isoformat(),
            "dimensions": ["marker_level_1"],
            "metrics": ["visitCount", "leadCount", "cost"],
        })
        return {
            "api_key_set": bool(s.ROISTAT_API_KEY),
            "api_key_length": len(s.ROISTAT_API_KEY),
            "project_id": s.ROISTAT_PROJECT_ID,
            "raw_response": raw,
        }
    except Exception as e:
        return {
            "api_key_set": bool(s.ROISTAT_API_KEY),
            "api_key_length": len(s.ROISTAT_API_KEY),
            "project_id": s.ROISTAT_PROJECT_ID,
            "error": str(e),
            "error_type": type(e).__name__,
        }
