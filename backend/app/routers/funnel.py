"""
/api/funnel — Marketing + Sales funnel.
Marketing data from Roistat, sales from Bitrix24.
Conversions: лид → осмотр → монтаж.
"""
from fastapi import APIRouter, Depends, Query
from datetime import datetime, timedelta, date
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.database import get_db
from app.models import Lead, Deal, Visit, RoistatChannel
from app.config import get_settings

router = APIRouter()
settings = get_settings()


def parse_date(val: str | None) -> date | None:
    if not val:
        return None
    try:
        return date.fromisoformat(val)
    except (ValueError, TypeError):
        return None


@router.get("/funnel/marketing")
def get_marketing(
    date_from: str = Query(None),
    date_to: str = Query(None),
    db: Session = Depends(get_db),
):
    """Marketing metrics from Roistat cache."""
    today = date.today()
    d_from = parse_date(date_from) or today.replace(day=1)
    d_to = parse_date(date_to) or today

    # Aggregated channel data
    result = db.execute(
        select(
            RoistatChannel.channel_name,
            func.sum(RoistatChannel.visits).label("visits"),
            func.sum(RoistatChannel.leads).label("leads"),
            func.sum(RoistatChannel.cost_with_vat).label("cost"),
            func.sum(RoistatChannel.calls).label("calls"),
            func.sum(RoistatChannel.sales).label("sales"),
            func.sum(RoistatChannel.revenue).label("revenue"),
        ).where(
            RoistatChannel.date >= d_from,
            RoistatChannel.date <= d_to,
        ).group_by(
            RoistatChannel.channel_name,
        ).order_by(
            func.sum(RoistatChannel.leads).desc(),
        )
    )
    channels = result.all()

    total_cost = sum(c.cost or 0 for c in channels)
    total_leads = sum(c.leads or 0 for c in channels)
    total_revenue = sum(c.revenue or 0 for c in channels)

    return {
        "period": f"{d_from.isoformat()} — {d_to.isoformat()}",
        "totals": {
            "cost": round(total_cost, 0),
            "leads": total_leads,
            "cpl": round(total_cost / total_leads, 0) if total_leads > 0 else 0,
            "roi": round((total_revenue - total_cost) / total_cost * 100, 1) if total_cost > 0 else None,
        },
        "channels": [
            {
                "name": c.channel_name,
                "visits": c.visits or 0,
                "leads": c.leads or 0,
                "cost": round(c.cost or 0, 0),
                "cpl": round((c.cost or 0) / c.leads, 0) if c.leads else 0,
                "calls": c.calls or 0,
                "conversion": round(c.leads / c.visits * 100, 1) if c.visits else 0,
                "sales": c.sales or 0,
                "revenue": round(c.revenue or 0, 0),
                "roi": round(((c.revenue or 0) - (c.cost or 0)) / (c.cost or 1) * 100, 1) if c.cost else None,
            }
            for c in channels
        ],
    }


@router.get("/funnel/sales")
def get_sales(
    date_from: str = Query(None),
    date_to: str = Query(None),
    db: Session = Depends(get_db),
):
    """Sales funnel — deal stages + conversions."""
    today = date.today()
    d_from = parse_date(date_from) or (today - timedelta(days=30))
    d_to = parse_date(date_to) or today
    cutoff = datetime.combine(d_from, datetime.min.time())
    cutoff_end = datetime.combine(d_to, datetime.max.time())

    # Deals by stage (active deals — no date filter, shows current state)
    stages = db.execute(
        select(
            Deal.stage_name,
            func.count(Deal.id).label("count"),
            func.sum(Deal.amount).label("total"),
        ).where(
            Deal.is_won == False,
            Deal.is_lost == False,
            Deal.category_id == 7,
        ).group_by(Deal.stage_name)
    )
    stage_data = [
        {"stage": s.stage_name, "count": s.count, "total": round(s.total or 0, 0)}
        for s in stages.all()
    ]

    # Lead rejection reasons (filtered by period)
    rejections = db.execute(
        select(
            Lead.rejection_reason,
            func.count(Lead.id).label("count"),
        ).where(
            Lead.rejection_reason.isnot(None),
            Lead.created_at >= cutoff,
            Lead.created_at <= cutoff_end,
        ).group_by(Lead.rejection_reason).order_by(func.count(Lead.id).desc())
    )
    rejection_data = [
        {"reason": r.rejection_reason, "count": r.count}
        for r in rejections.all()
    ]

    return {
        "stages": stage_data,
        "rejections": rejection_data,
    }


@router.get("/funnel/conversions")
def get_conversions(
    group_by: str = Query(None, regex="^(manager|direction)$"),
    date_from: str = Query(None),
    date_to: str = Query(None),
    db: Session = Depends(get_db),
):
    """
    Conversion funnel: лид → осмотр → монтаж.
    Optional grouping by manager or direction.
    """
    today = date.today()
    d_from = parse_date(date_from) or (today - timedelta(days=30))
    d_to = parse_date(date_to) or today
    cutoff = datetime.combine(d_from, datetime.min.time())
    cutoff_end = datetime.combine(d_to, datetime.max.time())

    # Inspections (unique per deal_id)
    inspections_q = select(Visit).where(
        Visit.visit_type.in_(["О"]),
        Visit.is_completed == True,
        Visit.created_at >= cutoff,
        Visit.created_at <= cutoff_end,
    )
    inspections = (db.execute(inspections_q)).scalars().all()
    unique_inspections = {v.deal_id: v for v in inspections if v.deal_id}

    # Montages (unique per deal_id)
    montages_q = select(Visit).where(
        Visit.visit_type.in_(["М", "M"]),
        Visit.is_completed == True,
        Visit.created_at >= cutoff,
        Visit.created_at <= cutoff_end,
    )
    montages = (db.execute(montages_q)).scalars().all()
    unique_montages = {v.deal_id: v for v in montages if v.deal_id}

    if not group_by:
        # No grouping — just count leads and return totals
        leads_count = db.execute(
            select(func.count(Lead.id)).where(
                Lead.created_at >= cutoff,
                Lead.created_at <= cutoff_end,
            )
        )
        total_leads = leads_count.scalar() or 0
        n_insp = len(unique_inspections)
        n_mont = len(unique_montages)
        return {
            "leads": total_leads,
            "inspections": n_insp,
            "montages": n_mont,
            "conv_lead_inspection": round(n_insp / total_leads * 100, 1) if total_leads else 0,
            "conv_inspection_montage": round(n_mont / n_insp * 100, 1) if n_insp else 0,
            "conv_lead_montage": round(n_mont / total_leads * 100, 1) if total_leads else 0,
        }

    # Grouped conversions — fetch all leads once, reuse for both branches
    from collections import defaultdict
    leads_q = select(Lead).where(Lead.created_at >= cutoff, Lead.created_at <= cutoff_end)
    all_leads = (db.execute(leads_q)).scalars().all()
    groups = defaultdict(lambda: {"leads": 0, "inspections": set(), "montages": set()})

    if group_by == "manager":
        for l in all_leads:
            groups[l.assigned_by]["leads"] += 1
        for v in inspections:
            if v.deal_id:
                groups[v.assigned_manager]["inspections"].add(v.deal_id)
        for v in montages:
            if v.deal_id:
                groups[v.assigned_manager]["montages"].add(v.deal_id)

        # Separate ROP from managers
        rop_name = settings.ROP
        manager_names = settings.MANAGERS
        rop_data = None
        manager_result = {}

        for key, data in groups.items():
            n_l = data["leads"]
            n_i = len(data["inspections"])
            n_m = len(data["montages"])
            entry = {
                "leads": n_l,
                "inspections": n_i,
                "montages": n_m,
                "conv_lead_inspection": round(n_i / n_l * 100, 1) if n_l else 0,
                "conv_inspection_montage": round(n_m / n_i * 100, 1) if n_i else 0,
                "conv_lead_montage": round(n_m / n_l * 100, 1) if n_l else 0,
            }
            if key == rop_name:
                rop_data = entry
            elif key in manager_names:
                manager_result[key] = entry
            else:
                # Unknown users (ID:36183 etc) — include in managers table
                manager_result[key] = entry

        # ROP lead breakdown by status (using STATUS_SEMANTIC_ID: S=success, F=fail, P=process)
        rop_breakdown = None
        if rop_data:
            rop_leads = [l for l in all_leads if l.assigned_by == rop_name]
            converted = sum(1 for l in rop_leads if l.is_converted)
            rejected = sum(1 for l in rop_leads if l.is_rejected)
            in_work = len(rop_leads) - converted - rejected
            rop_breakdown = {
                "total": len(rop_leads),
                "in_work": in_work,
                "converted": converted,
                "rejected": rejected,
            }

        return {
            "group_by": group_by,
            "data": manager_result,
            "rop": {
                "name": rop_name,
                "metrics": rop_data,
                "breakdown": rop_breakdown,
            } if rop_data else None,
        }

    # group_by == "direction"
    for l in all_leads:
        groups[l.direction or "Неизвестно"]["leads"] += 1

    # Build deal_id -> direction map from deals table
    deal_directions = {}
    deal_rows = db.execute(
        select(Deal.id, Deal.direction).where(
            Deal.direction.isnot(None),
            Deal.direction != "",
        )
    ).all()
    for row in deal_rows:
        deal_directions[row[0]] = row[1]

    # Assign inspections/montages to direction via linked deal
    for v in inspections:
        if v.deal_id:
            direction = deal_directions.get(v.deal_id, "Неизвестно")
            groups[direction]["inspections"].add(v.deal_id)
    for v in montages:
        if v.deal_id:
            direction = deal_directions.get(v.deal_id, "Неизвестно")
            groups[direction]["montages"].add(v.deal_id)

    result = {}
    for key, data in groups.items():
        n_l = data["leads"]
        n_i = len(data["inspections"])
        n_m = len(data["montages"])
        result[key] = {
            "leads": n_l,
            "inspections": n_i,
            "montages": n_m,
            "conv_lead_inspection": round(n_i / n_l * 100, 1) if n_l else 0,
            "conv_inspection_montage": round(n_m / n_i * 100, 1) if n_i else 0,
            "conv_lead_montage": round(n_m / n_l * 100, 1) if n_l else 0,
        }

    return {"group_by": group_by, "data": result}
