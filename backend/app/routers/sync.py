"""
/api/sync — Data synchronization endpoints.
Triggers loading data from Bitrix24 and Roistat into PostgreSQL.
"""
from fastapi import APIRouter, Query
from datetime import datetime
from app.services.sync import run_full_sync, sync_leads, sync_deals, sync_visits, sync_roistat, get_sync_status
from app.database import SessionLocal

router = APIRouter()


@router.get("/sync/status")
def sync_status():
    """Get current sync status — use this to check data freshness."""
    return get_sync_status()


@router.post("/sync/run")
def trigger_full_sync(days_back: int = Query(90, ge=0, le=365)):
    """
    Run full data sync from all Phase 1 sources.
    days_back=0 means load ALL Bitrix24 data (no date filter).
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
            "period": {
                "from": f"{(date.today() - timedelta(days=7)).isoformat()}T00:00:00+0300",
                "to": f"{date.today().isoformat()}T23:59:59+0300",
            },
            "dimensions": ["marker_level_1"],
            "metrics": ["visits", "leads", "marketing_cost"],
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


@router.get("/sync/debug-leads")
def debug_leads():
    """Debug: show lead status distribution for ROP to find is_rejected issues."""
    from sqlalchemy import select, func
    from app.models import Lead
    from app.config import get_settings
    settings = get_settings()
    db = SessionLocal()
    try:
        rop_name = settings.ROP

        # All leads assigned to ROP — group by status_id, is_rejected, is_converted
        status_breakdown = db.execute(
            select(
                Lead.status_id,
                Lead.status_name,
                Lead.is_rejected,
                Lead.is_converted,
                func.count(Lead.id).label("count"),
            ).where(
                Lead.assigned_by == rop_name,
            ).group_by(
                Lead.status_id, Lead.status_name, Lead.is_rejected, Lead.is_converted,
            ).order_by(func.count(Lead.id).desc())
        ).all()

        # Same but only for "in work" (not rejected, not converted)
        in_work_statuses = db.execute(
            select(
                Lead.status_id,
                Lead.status_name,
                func.count(Lead.id).label("count"),
            ).where(
                Lead.assigned_by == rop_name,
                Lead.is_rejected == False,
                Lead.is_converted == False,
            ).group_by(
                Lead.status_id, Lead.status_name,
            ).order_by(func.count(Lead.id).desc())
        ).all()

        return {
            "rop_name": rop_name,
            "total_rop_leads": sum(r.count for r in status_breakdown),
            "all_statuses": [
                {
                    "status_id": r.status_id,
                    "status_name": r.status_name,
                    "is_rejected": r.is_rejected,
                    "is_converted": r.is_converted,
                    "count": r.count,
                }
                for r in status_breakdown
            ],
            "in_work_detail": [
                {
                    "status_id": r.status_id,
                    "status_name": r.status_name,
                    "count": r.count,
                }
                for r in in_work_statuses
            ],
            "total_in_work": sum(r.count for r in in_work_statuses),
        }
    finally:
        db.close()
