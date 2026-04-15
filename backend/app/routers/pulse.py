"""
/api/pulse — Main dashboard screen.
Aggregates key metrics from all sources.
"""
from fastapi import APIRouter, Depends, Query
from datetime import datetime, timedelta, date
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.database import get_db
from app.models import Lead, Deal, Visit, RoistatChannel, SalesPlan
from app.services.sync import get_sync_status
from app.config import get_settings

router = APIRouter()
settings = get_settings()


def parse_date_param(val: str | None) -> date | None:
    if not val:
        return None
    try:
        return date.fromisoformat(val)
    except (ValueError, TypeError):
        return None


@router.get("/pulse")
def get_pulse(
    date_from: str = Query(None),
    date_to: str = Query(None),
    db: Session = Depends(get_db),
):
    """
    Main pulse screen data.
    Optional date_from/date_to (ISO format) for custom period.
    Defaults to current month if not provided.
    """
    today = date.today()
    d_from = parse_date_param(date_from)
    d_to = parse_date_param(date_to)

    # If both dates provided, use custom period
    if d_from and d_to:
        period_start = d_from
        period_end = d_to
    else:
        period_start = today.replace(day=1)
        period_end = today

    yesterday = today - timedelta(days=1)
    week_ago = today - timedelta(days=7)
    period_start_dt = datetime.combine(period_start, datetime.min.time())
    period_end_dt = datetime.combine(period_end, datetime.max.time())

    # --- Revenue yesterday (closed deals) ---
    # CLOSEDATE = correct close date in Bitrix24 (matches UI filter "Дата завершения")
    revenue_yesterday = db.execute(
        select(func.sum(Deal.amount)).where(
            Deal.is_won == True,
            func.date(Deal.closed_at) == yesterday,
        )
    )
    revenue_yesterday_val = revenue_yesterday.scalar() or 0

    # --- New leads yesterday ---
    leads_yesterday = db.execute(
        select(func.count(Lead.id)).where(
            func.date(Lead.created_at) == yesterday,
        )
    )
    leads_yesterday_val = leads_yesterday.scalar() or 0

    # --- Leads this week ---
    leads_week = db.execute(
        select(func.count(Lead.id)).where(
            Lead.created_at >= datetime.combine(week_ago, datetime.min.time()),
        )
    )
    leads_week_val = leads_week.scalar() or 0

    # --- Closed deals yesterday ---
    closed_yesterday = db.execute(
        select(func.count(Deal.id)).where(
            Deal.is_won == True,
            func.date(Deal.closed_at) == yesterday,
        )
    )
    closed_yesterday_val = closed_yesterday.scalar() or 0

    # --- Montages completed yesterday (from visits funnel) ---
    montages_yesterday = db.execute(
        select(func.count(Visit.id)).where(
            Visit.visit_type.in_(["М", "M"]),
            Visit.is_completed == True,
            func.date(Visit.completed_at) == yesterday,
        )
    )
    montages_yesterday_val = montages_yesterday.scalar() or 0

    # --- Red flags ---
    # Stale deals (no activity > 7 days)
    stale_cutoff = datetime.utcnow() - timedelta(days=7)
    stale_deals = db.execute(
        select(func.count(Deal.id)).where(
            Deal.last_activity_at < stale_cutoff,
            Deal.is_won == False,
            Deal.is_lost == False,
        )
    )
    stale_deals_val = stale_deals.scalar() or 0

    # Stuck montages
    stuck_montages = db.execute(
        select(func.count(Deal.id)).where(
            Deal.stage_name.ilike("%монтаж завис%"),
        )
    )
    stuck_montages_val = stuck_montages.scalar() or 0

    # --- Funnel snapshot ---
    active_leads = db.execute(
        select(func.count(Lead.id)).where(
            Lead.is_converted == False,
            Lead.status_id.notin_(["JUNK", "CONVERTED"]),
        )
    )
    active_leads_val = active_leads.scalar() or 0

    active_deals = db.execute(
        select(func.count(Deal.id)).where(
            Deal.is_won == False,
            Deal.is_lost == False,
            Deal.category_id == 7,
        )
    )
    active_deals_val = active_deals.scalar() or 0

    # --- Sales plan ---
    # Sum plans for all months covered by the selected period
    # E.g. if period is Jan-Mar, sum plans for months 1, 2, 3
    from calendar import monthrange
    plan_months = set()
    cursor = period_start
    while cursor <= period_end:
        plan_months.add((cursor.year, cursor.month))
        # Move to first day of next month
        if cursor.month == 12:
            cursor = date(cursor.year + 1, 1, 1)
        else:
            cursor = date(cursor.year, cursor.month + 1, 1)

    plan_amount = 0
    for p_year, p_month in plan_months:
        plan = db.execute(
            select(SalesPlan).where(
                SalesPlan.year == p_year,
                SalesPlan.month == p_month,
            )
        )
        plan_row = plan.scalar_one_or_none()
        if plan_row:
            plan_amount += plan_row.plan_amount

    # Monthly revenue (by deals) — CLOSEDATE = "Дата завершения" in Bitrix24
    monthly_gross = db.execute(
        select(func.sum(Deal.amount)).where(
            Deal.is_won == True,
            Deal.closed_at >= period_start_dt,
            Deal.closed_at <= period_end_dt,
        )
    )
    monthly_gross_val = monthly_gross.scalar() or 0

    # --- Avg montage check (excluding deals below threshold) ---
    min_check = settings.MONTAGE_MIN_CHECK
    avg_check = db.execute(
        select(func.avg(Deal.amount)).where(
            Deal.is_won == True,
            Deal.amount >= min_check,
            Deal.closed_at >= period_start_dt,
            Deal.closed_at <= period_end_dt,
        )
    )
    avg_check_val = avg_check.scalar()
    avg_check_val = round(avg_check_val, 0) if avg_check_val else 0

    # --- Period leads count ---
    period_leads = db.execute(
        select(func.count(Lead.id)).where(
            Lead.created_at >= period_start_dt,
            Lead.created_at <= period_end_dt,
        )
    )
    period_leads_val = period_leads.scalar() or 0

    # --- Period closed deals count ---
    period_closed = db.execute(
        select(func.count(Deal.id)).where(
            Deal.is_won == True,
            Deal.closed_at >= period_start_dt,
            Deal.closed_at <= period_end_dt,
        )
    )
    period_closed_val = period_closed.scalar() or 0

    # --- Period montages ---
    period_montages = db.execute(
        select(func.count(Visit.id)).where(
            Visit.visit_type.in_(["М", "M"]),
            Visit.is_completed == True,
            Visit.completed_at >= period_start_dt,
            Visit.completed_at <= period_end_dt,
        )
    )
    period_montages_val = period_montages.scalar() or 0

    return {
        "date": today.isoformat(),
        "period": {"from": period_start.isoformat(), "to": period_end.isoformat()},
        "metrics": {
            "revenue_yesterday": revenue_yesterday_val,
            "leads_yesterday": leads_yesterday_val,
            "leads_week": leads_week_val,
            "closed_deals_yesterday": closed_yesterday_val,
            "montages_yesterday": montages_yesterday_val,
            "avg_montage_check": avg_check_val,
            "period_leads": period_leads_val,
            "period_closed": period_closed_val,
            "period_montages": period_montages_val,
            "period_revenue": monthly_gross_val,
        },
        "red_flags": {
            "stale_deals_7d": stale_deals_val,
            "stuck_montages": stuck_montages_val,
        },
        "funnel": {
            "active_leads": active_leads_val,
            "active_deals": active_deals_val,
        },
        "plan_fact": {
            "plan": plan_amount,
            "fact": monthly_gross_val,
            "percent": round(monthly_gross_val / plan_amount * 100, 1) if plan_amount > 0 else 0,
        },
        "sync": get_sync_status(),
    }
