"""
Funnel conversion calculations.
Core conversions: лид → осмотр → монтаж
Per manager, per installer, per direction.
"""
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional


def calculate_conversions(
    leads: list,
    visits: list,
    deals: list,
    group_by: str = None,  # "manager", "installer", "direction"
    period_days: int = 30,
) -> dict:
    """
    Calculate лид→осмотр→монтаж conversions.

    Args:
        leads: List of lead dicts from Bitrix24
        visits: List of visit dicts from выезды funnel
        deals: List of deal dicts from sales funnel
        group_by: Optional grouping field
        period_days: Period to analyze

    Returns:
        Dict with conversion metrics
    """
    cutoff = datetime.utcnow() - timedelta(days=period_days)

    # Filter by period
    period_leads = [l for l in leads if _parse_date(l.get("created_at")) and _parse_date(l["created_at"]) >= cutoff]
    period_visits = [v for v in visits if v.get("visit_type") in ("О", "M", "М")]
    period_montages = [d for d in deals if d.get("is_won") or d.get("stage_name", "").startswith("Монтаж")]

    if not group_by:
        return _calc_group(period_leads, period_visits, period_montages)

    # Group by field
    groups = defaultdict(lambda: {"leads": [], "visits": [], "montages": []})

    field_map = {
        "manager": "assigned_by",
        "installer": "assigned_installer",
        "direction": "direction",
    }
    field = field_map.get(group_by, group_by)

    for lead in period_leads:
        key = lead.get(field, "Неизвестно")
        groups[key]["leads"].append(lead)

    for visit in period_visits:
        key = visit.get(field, "Неизвестно")
        groups[key]["visits"].append(visit)

    for deal in period_montages:
        key = deal.get(field, "Неизвестно")
        groups[key]["montages"].append(deal)

    result = {}
    for key, data in groups.items():
        result[key] = _calc_group(data["leads"], data["visits"], data["montages"])

    return result


def _calc_group(leads: list, visits: list, montages: list) -> dict:
    """Calculate conversion metrics for a group."""
    n_leads = len(leads)
    n_visits = len(visits)
    n_montages = len(montages)

    # Deduplicate visits by deal_id (one inspection per deal)
    unique_visits = {}
    for v in visits:
        deal_id = v.get("deal_id")
        if deal_id and deal_id not in unique_visits:
            unique_visits[deal_id] = v
        elif not deal_id:
            unique_visits[v.get("id", id(v))] = v
    n_unique_visits = len(unique_visits)

    # Deduplicate montages by deal_id
    unique_montages = {}
    for m in montages:
        deal_id = m.get("deal_id", m.get("id"))
        if deal_id and deal_id not in unique_montages:
            unique_montages[deal_id] = m
    n_unique_montages = len(unique_montages)

    return {
        "leads": n_leads,
        "inspections": n_unique_visits,
        "montages": n_unique_montages,
        "conv_lead_to_inspection": round(n_unique_visits / n_leads * 100, 1) if n_leads > 0 else 0,
        "conv_inspection_to_montage": round(n_unique_montages / n_unique_visits * 100, 1) if n_unique_visits > 0 else 0,
        "conv_lead_to_montage": round(n_unique_montages / n_leads * 100, 1) if n_leads > 0 else 0,
    }


def calculate_lead_response_time(leads_with_activities: list) -> dict:
    """
    Calculate average lead response time per manager.

    Args:
        leads_with_activities: List of dicts with
            'created_at', 'first_activity_at', 'assigned_by'

    Returns:
        Dict: {manager_name: avg_minutes}
    """
    manager_times = defaultdict(list)

    for lead in leads_with_activities:
        created = _parse_date(lead.get("created_at"))
        first_act = _parse_date(lead.get("first_activity_at"))
        manager = lead.get("assigned_by", "Unknown")

        if created and first_act and first_act > created:
            delta = (first_act - created).total_seconds() / 60
            if delta < 1440:  # Exclude > 24 hours (likely data issue)
                manager_times[manager].append(delta)

    return {
        mgr: round(sum(times) / len(times), 1)
        for mgr, times in manager_times.items()
        if times
    }


def calculate_avg_deal_cycle(deals: list) -> float:
    """Calculate average deal cycle in days (created → won)."""
    cycles = []
    for deal in deals:
        created = _parse_date(deal.get("created_at"))
        closed = _parse_date(deal.get("closed_at"))
        if created and closed and deal.get("is_won"):
            days = (closed - created).days
            if 0 < days < 365:
                cycles.append(days)

    return round(sum(cycles) / len(cycles), 1) if cycles else 0


def calculate_avg_montage_check(deals: list, min_amount: int = 15000) -> float:
    """
    Calculate average montage check, excluding small deals.
    min_amount: threshold to exclude (default 15000 RUB).
    """
    amounts = [
        d.get("amount", 0)
        for d in deals
        if d.get("is_won") and d.get("amount", 0) >= min_amount
    ]
    return round(sum(amounts) / len(amounts), 0) if amounts else 0


def _parse_date(dt_str) -> Optional[datetime]:
    """Parse datetime from various formats."""
    if isinstance(dt_str, datetime):
        return dt_str
    if not dt_str:
        return None
    try:
        # Try ISO format first
        return datetime.fromisoformat(str(dt_str).replace("Z", "+00:00").replace("+00:00", ""))
    except (ValueError, TypeError):
        return None
