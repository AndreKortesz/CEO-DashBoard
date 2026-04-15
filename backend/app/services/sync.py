"""
Data synchronization service.
Pulls data from Bitrix24 and Roistat, maps fields, saves to PostgreSQL.
Triggered via /api/sync/run endpoint or scheduled.
"""
import re
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from app.config import get_settings
from app.database import SessionLocal
from app.models import Lead, Deal, Visit, RoistatChannel
from app.services.bitrix24 import bitrix24_service as bx
from app.services.roistat import roistat_service as roistat

settings = get_settings()

# Global sync status — accessible from API endpoints
_sync_status = {
    "last_sync_at": None,
    "last_sync_duration_sec": None,
    "last_sync_status": "never",
    "last_sync_error": None,
    "is_running": False,
}


def get_sync_status() -> dict:
    """Get current sync status for API responses."""
    from datetime import datetime
    status = dict(_sync_status)
    if status["last_sync_at"]:
        age_sec = (datetime.utcnow() - status["last_sync_at"]).total_seconds()
        status["data_age_minutes"] = round(age_sec / 60, 1)
        status["is_stale"] = age_sec > 20 * 60  # stale if >20 min
        status["last_sync_at"] = status["last_sync_at"].isoformat()
    else:
        status["data_age_minutes"] = None
        status["is_stale"] = True
    return status


def parse_dt(val) -> datetime | None:
    """Parse Bitrix24 datetime string to Python datetime."""
    if not val:
        return None
    if isinstance(val, datetime):
        return val
    try:
        # Remove timezone info for simplicity
        clean = str(val).replace("T", " ").split("+")[0].split(".")[0]
        return datetime.fromisoformat(clean)
    except (ValueError, TypeError):
        return None


def resolve_direction(raw_value, direction_map: dict) -> str:
    """Resolve enumeration ID(s) to direction name(s) — comma-separated."""
    if not raw_value:
        return ""
    if isinstance(raw_value, list):
        names = [direction_map.get(str(v), "") for v in raw_value]
        return ", ".join(n for n in names if n) or ""
    return direction_map.get(str(raw_value), "")


def resolve_direction_first(raw_value, direction_map: dict) -> str:
    """Resolve enumeration ID(s) to FIRST direction name only."""
    if not raw_value:
        return ""
    if isinstance(raw_value, list):
        for v in raw_value:
            name = direction_map.get(str(v), "")
            if name:
                return name
        return ""
    return direction_map.get(str(raw_value), "")


def extract_deal_id_from_link(link_value) -> int | None:
    """Extract deal ID from Bitrix24 deal link URL."""
    if not link_value:
        return None
    # URL like: https://svyaz.bitrix24.ru/crm/deal/details/12345/
    match = re.search(r"/deal/details/(\d+)", str(link_value))
    if match:
        return int(match.group(1))
    return None


# =============================================================
# SYNC LEADS
# =============================================================

def sync_leads(db: Session, days_back: int = 90) -> dict:
    """Sync leads from Bitrix24 to PostgreSQL."""
    print(f"[SYNC] Starting leads sync (last {days_back} days)...")

    date_from = datetime.utcnow() - timedelta(days=days_back)
    raw_leads = bx.get_leads(date_from=date_from)
    lead_status_map = bx.get_lead_status_map()

    count_new = 0
    count_updated = 0

    for raw in raw_leads:
        lead_id = int(raw.get("ID", 0))
        if not lead_id:
            continue

        existing = db.get(Lead, lead_id)
        is_new = existing is None

        lead = existing or Lead(id=lead_id)
        lead.title = raw.get("TITLE", "")
        lead.status_id = raw.get("STATUS_ID", "")
        lead.status_name = lead_status_map.get(lead.status_id, lead.status_id)
        lead.source_id = raw.get("SOURCE_ID", "")
        lead.assigned_by = bx.resolve_user(raw.get("ASSIGNED_BY_ID"))
        lead.direction = resolve_direction_first(
            raw.get(settings.BX_LEAD_DIRECTION_FIELD),
            settings.BX_LEAD_DIRECTION_MAP,
        )
        lead.amount = float(raw.get("OPPORTUNITY", 0) or 0)
        lead.created_at = parse_dt(raw.get("DATE_CREATE"))
        lead.closed_at = parse_dt(raw.get("DATE_CLOSED"))
        lead.is_converted = raw.get("STATUS_SEMANTIC_ID") == "S"
        lead.is_rejected = raw.get("STATUS_SEMANTIC_ID") == "F"
        lead.rejection_reason = raw.get(settings.BX_LEAD_REJECTION_FIELD, "")
        lead.updated_at = datetime.utcnow()

        # DATE_MODIFY = first time manager touched the lead (better proxy than LAST_ACTIVITY)
        lead.first_activity_at = parse_dt(raw.get("DATE_MODIFY"))

        if is_new:
            db.add(lead)
            count_new += 1
        else:
            count_updated += 1

    db.commit()
    result = {"leads_new": count_new, "leads_updated": count_updated, "leads_total": len(raw_leads)}
    print(f"[SYNC] Leads: {result}")
    return result


# =============================================================
# SYNC DEALS (category_id=7)
# =============================================================

def sync_deals(db: Session, days_back: int = 180) -> dict:
    """Sync deals from Bitrix24 main funnel to PostgreSQL."""
    print(f"[SYNC] Starting deals sync (last {days_back} days)...")

    date_from = datetime.utcnow() - timedelta(days=days_back)
    # Fetch deals created recently
    raw_deals_created = bx.get_deals(category_id=settings.DEALS_CATEGORY_ID, date_from=date_from)
    # Also fetch deals MODIFIED recently (catches old deals that were just closed/won)
    raw_deals_modified = bx.get_deals(category_id=settings.DEALS_CATEGORY_ID, date_modify_from=date_from)
    # Merge and deduplicate by ID
    seen_ids = set()
    raw_deals = []
    for deal in raw_deals_created + raw_deals_modified:
        did = deal.get("ID")
        if did and did not in seen_ids:
            seen_ids.add(did)
            raw_deals.append(deal)
    print(f"[SYNC] Deals: {len(raw_deals_created)} by created + {len(raw_deals_modified)} by modified = {len(raw_deals)} unique")
    stage_map = bx.get_stage_map(settings.DEALS_CATEGORY_ID)

    count_new = 0
    count_updated = 0

    for raw in raw_deals:
        deal_id = int(raw.get("ID", 0))
        if not deal_id:
            continue

        existing = db.get(Deal, deal_id)
        is_new = existing is None

        deal = existing or Deal(id=deal_id)
        deal.title = raw.get("TITLE", "")
        deal.stage_id = raw.get("STAGE_ID", "")
        deal.stage_name = stage_map.get(deal.stage_id, deal.stage_id)
        deal.category_id = int(raw.get("CATEGORY_ID", 7))
        deal.assigned_by = bx.resolve_user(raw.get("ASSIGNED_BY_ID"))
        deal.amount = float(raw.get("OPPORTUNITY", 0) or 0)
        deal.created_at = parse_dt(raw.get("DATE_CREATE"))
        deal.closed_at = parse_dt(raw.get("CLOSEDATE"))
        deal.last_activity_at = parse_dt(raw.get("DATE_MODIFY"))
        deal.is_won = raw.get("STAGE_SEMANTIC_ID") == "S"
        deal.is_lost = raw.get("STAGE_SEMANTIC_ID") == "F"
        deal.loss_reason = raw.get(settings.BX_DEAL_REJECTION_FIELD, "")
        deal.is_repeat = bool(raw.get(settings.BX_DEAL_IS_COPY_FIELD))
        deal.updated_at = datetime.utcnow()

        # Direction from "Вид услуг" on DEALS — different field than leads!
        deal.direction = resolve_direction_first(
            raw.get(settings.BX_DEAL_DIRECTION_FIELD),
            settings.BX_DEAL_DIRECTION_MAP,
        )

        # Try to get area
        area_raw = raw.get(settings.BX_DEAL_AREA_FIELD, "")
        if area_raw:
            try:
                deal.area_sqm = float(str(area_raw).replace(",", ".").strip())
            except (ValueError, TypeError):
                pass

        if is_new:
            db.add(deal)
            count_new += 1
        else:
            count_updated += 1

    db.commit()
    result = {"deals_new": count_new, "deals_updated": count_updated, "deals_total": len(raw_deals)}
    print(f"[SYNC] Deals: {result}")
    return result


# =============================================================
# SYNC VISITS (category_id=45)
# =============================================================

def sync_visits(db: Session, days_back: int = 180) -> dict:
    """Sync visits from Bitrix24 visits funnel to PostgreSQL."""
    print(f"[SYNC] Starting visits sync (last {days_back} days)...")

    date_from = datetime.utcnow() - timedelta(days=days_back)
    raw_visits = bx.get_visits(date_from=date_from)
    stage_map = bx.get_stage_map(settings.VISITS_CATEGORY_ID)

    count_new = 0
    count_updated = 0

    for raw in raw_visits:
        visit_id = int(raw.get("ID", 0))
        if not visit_id:
            continue

        existing = db.get(Visit, visit_id)
        is_new = existing is None

        visit = existing or Visit(id=visit_id)
        visit.title = raw.get("TITLE", "")
        visit.stage_id = raw.get("STAGE_ID", "")
        visit.stage_name = stage_map.get(visit.stage_id, visit.stage_id)

        # Visit type from UF field
        visit_type_raw = raw.get(settings.BX_VISIT_TYPE_FIELD)
        visit.visit_type = settings.BX_VISIT_TYPE_MAP.get(
            str(visit_type_raw), ""
        ) if visit_type_raw else ""

        # If no UF field, try to parse from title prefix
        if not visit.visit_type and visit.title:
            title_lower = visit.title.lower().strip()
            if title_lower.startswith("м") or "монтаж" in title_lower:
                visit.visit_type = "М"
            elif title_lower.startswith("о") or "осмотр" in title_lower:
                visit.visit_type = "О"
            elif title_lower.startswith("г") or "гарантия" in title_lower:
                visit.visit_type = "Г"
            elif "диагн" in title_lower:
                visit.visit_type = "Диагн"

        # Link to main deal
        deal_link = raw.get(settings.BX_VISIT_DEAL_LINK_FIELD)
        visit.deal_id = extract_deal_id_from_link(deal_link)

        # Installer / inspector
        inspector_id = raw.get(settings.BX_INSPECTOR_FIELD)
        installer_id = raw.get(settings.BX_INSTALLER_FIELD)
        visit.assigned_installer = bx.resolve_user(installer_id or inspector_id)
        visit.assigned_manager = bx.resolve_user(raw.get("ASSIGNED_BY_ID"))

        visit.amount = float(raw.get("OPPORTUNITY", 0) or 0)
        visit.created_at = parse_dt(raw.get("DATE_CREATE"))
        visit.completed_at = parse_dt(raw.get("CLOSEDATE"))
        visit.is_completed = raw.get("STAGE_SEMANTIC_ID") == "S"
        visit.is_failed = "не произведен" in (visit.stage_name or "").lower()
        visit.scheduled_at = parse_dt(raw.get("DATE_CREATE"))  # Approximation
        visit.updated_at = datetime.utcnow()

        if is_new:
            db.add(visit)
            count_new += 1
        else:
            count_updated += 1

    db.commit()
    result = {"visits_new": count_new, "visits_updated": count_updated, "visits_total": len(raw_visits)}
    print(f"[SYNC] Visits: {result}")
    return result


# =============================================================
# SYNC ROISTAT CHANNELS
# =============================================================

def sync_roistat(db: Session, days_back: int = 30) -> dict:
    """Sync Roistat channel data to PostgreSQL — per day granularity.
    Fetches each day separately so historical data is preserved.
    For auto-sync (days_back=30) only re-fetches last 3 days to save API calls.
    """
    print(f"[SYNC] Starting Roistat sync (last {days_back} days)...")

    today = date.today()

    # Auto-sync: only refresh last 3 days (data may be adjusted by Roistat)
    # Manual sync (days_back > 30): refresh full range
    refresh_days = min(days_back, 3) if days_back <= 30 else days_back
    date_from = today - timedelta(days=refresh_days)

    count = 0
    errors = []

    current_day = date_from
    while current_day <= today:
        try:
            channels = roistat.get_channel_summary(current_day, current_day)
        except Exception as e:
            errors.append(f"{current_day}: {e}")
            print(f"[SYNC] Roistat error for {current_day}: {e}")
            current_day += timedelta(days=1)
            continue

        for ch in channels:
            # Upsert: check if exists for this day + channel
            existing = db.query(RoistatChannel).filter(
                RoistatChannel.date == current_day,
                RoistatChannel.channel_name == ch["channel_name"],
            ).first()

            if existing:
                rec = existing
            else:
                rec = RoistatChannel(date=current_day, channel_name=ch["channel_name"])
                db.add(rec)

            rec.visits = ch["visits"]
            rec.leads = ch["leads"]
            rec.calls = ch["calls"]
            rec.cost_without_vat = ch["cost_without_vat"]
            rec.cost_with_vat = ch["cost_with_vat"]
            rec.cpl = ch["cpl"]
            rec.conversion_rate = ch["conversion_rate"]
            rec.sales = ch["sales"]
            rec.revenue = ch["revenue"]
            rec.updated_at = datetime.utcnow()
            count += 1

        current_day += timedelta(days=1)

    db.commit()
    result = {"roistat_channels": count, "days_synced": refresh_days + 1}
    if errors:
        result["errors"] = errors
    print(f"[SYNC] Roistat: {result}")
    return result


# =============================================================
# FULL SYNC
# =============================================================

def run_full_sync(days_back: int = 90) -> dict:
    """Run full synchronization of all Phase 1 data sources."""
    global _sync_status
    started = datetime.utcnow()
    _sync_status["is_running"] = True
    print(f"[SYNC] === Full sync started at {started.isoformat()} ===")
    db = SessionLocal()
    results = {}

    try:
        results["leads"] = sync_leads(db, days_back=days_back)
        results["deals"] = sync_deals(db, days_back=days_back)
        results["visits"] = sync_visits(db, days_back=days_back)
        results["roistat"] = sync_roistat(db, days_back=30)
        results["status"] = "ok"
        _sync_status["last_sync_status"] = "ok"
        _sync_status["last_sync_error"] = None
    except Exception as e:
        results["status"] = "error"
        results["error"] = str(e)
        _sync_status["last_sync_status"] = "error"
        _sync_status["last_sync_error"] = str(e)
        print(f"[SYNC] ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
        _sync_status["is_running"] = False
        _sync_status["last_sync_at"] = datetime.utcnow()
        _sync_status["last_sync_duration_sec"] = round(
            (datetime.utcnow() - started).total_seconds(), 1
        )

    print(f"[SYNC] === Full sync finished: {results.get('status')} ===")
    return results
