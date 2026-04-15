"""
/api/people — Managers + Installers.
Manager data from Bitrix24 + Rechka AI.
Installer data from Bitrix24 visits funnel.
"""
from fastapi import APIRouter, Depends, Query
from datetime import datetime, timedelta, date
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.database import get_db
from app.models import Lead, Deal, Visit, RechkaWeekly, RechkaCall
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


@router.get("/people/managers")
def get_managers(
    date_from: str = Query(None),
    date_to: str = Query(None),
    db: Session = Depends(get_db),
):
    """Manager performance data."""
    today = date.today()
    d_from = parse_date(date_from) or today.replace(day=1)
    d_to = parse_date(date_to) or today
    period_start = datetime.combine(d_from, datetime.min.time())
    period_end = datetime.combine(d_to, datetime.max.time())
    yesterday = today - timedelta(days=1)

    managers_data = []
    for manager in settings.MANAGERS:
        # Closed deals in period
        closed = db.execute(
            select(func.count(Deal.id), func.sum(Deal.amount)).where(
                Deal.assigned_by == manager,
                Deal.is_won == True,
                Deal.closed_at >= period_start,
                Deal.closed_at <= period_end,
            )
        )
        closed_row = closed.one()
        closed_count = closed_row[0] or 0
        closed_amount = closed_row[1] or 0

        # Average lead response time
        leads_with_activity = db.execute(
            select(
                Lead.created_at,
                Lead.first_activity_at,
            ).where(
                Lead.assigned_by == manager,
                Lead.first_activity_at.isnot(None),
                Lead.created_at >= period_start,
            )
        )
        response_times = []
        for row in leads_with_activity.all():
            if row[0] and row[1]:
                delta = (row[1] - row[0]).total_seconds() / 60
                if 0 < delta < 1440:
                    response_times.append(delta)
        avg_response = round(sum(response_times) / len(response_times), 0) if response_times else None

        # Overdue tasks count
        overdue = db.execute(
            select(func.count(Deal.id)).where(
                Deal.assigned_by == manager,
                Deal.is_won == False,
                Deal.is_lost == False,
                Deal.last_activity_at < datetime.utcnow() - timedelta(days=7),
            )
        )
        overdue_val = overdue.scalar() or 0

        # Latest Rechka score
        rechka = db.execute(
            select(RechkaWeekly).where(
                RechkaWeekly.manager_name == manager,
            ).order_by(RechkaWeekly.week_number.desc()).limit(1)
        )
        rechka_row = rechka.scalar_one_or_none()

        managers_data.append({
            "name": manager,
            "closed_deals": closed_count,
            "closed_amount": round(closed_amount, 0),
            "avg_response_minutes": avg_response,
            "overdue_tasks": overdue_val,
            "rechka": {
                "score_total": rechka_row.score_total if rechka_row else None,
                "score_contact": rechka_row.score_contact if rechka_row else None,
                "score_needs": rechka_row.score_needs if rechka_row else None,
                "score_pain": rechka_row.score_pain if rechka_row else None,
                "score_presentation": rechka_row.score_presentation if rechka_row else None,
                "score_objections": rechka_row.score_objections if rechka_row else None,
                "score_proposal": rechka_row.score_proposal if rechka_row else None,
                "score_mop_leader": rechka_row.score_mop_leader if rechka_row else None,
                "week": rechka_row.week_number if rechka_row else None,
            } if rechka_row else None,
        })

    # Department-level Rechka
    dept_rechka = db.execute(
        select(RechkaWeekly).where(
            RechkaWeekly.manager_name == "ОТДЕЛ",
        ).order_by(RechkaWeekly.week_number.desc()).limit(1)
    )
    dept_row = dept_rechka.scalar_one_or_none()

    return {
        "managers": managers_data,
        "rop": settings.ROP,
        "department_rechka": {
            "score_total": dept_row.score_total if dept_row else None,
            "week": dept_row.week_number if dept_row else None,
        } if dept_row else None,
    }


@router.get("/people/managers/{manager_name}")
def get_manager_detail(
    manager_name: str,
    date_from: str = Query(None),
    date_to: str = Query(None),
    db: Session = Depends(get_db),
):
    """Detailed manager card with Rechka history."""
    today = date.today()
    d_from = parse_date(date_from) or today.replace(day=1)
    d_to = parse_date(date_to) or today
    period_start = datetime.combine(d_from, datetime.min.time())
    period_end = datetime.combine(d_to, datetime.max.time())

    # Rechka weekly history (last 10 weeks)
    rechka_history = db.execute(
        select(RechkaWeekly).where(
            RechkaWeekly.manager_name == manager_name,
        ).order_by(RechkaWeekly.week_number.desc()).limit(10)
    )
    history = rechka_history.scalars().all()

    # Active deals by stage (current state — no date filter)
    deals_by_stage = db.execute(
        select(
            Deal.stage_name,
            func.count(Deal.id).label("count"),
            func.sum(Deal.amount).label("total"),
        ).where(
            Deal.assigned_by == manager_name,
            Deal.is_won == False,
            Deal.is_lost == False,
        ).group_by(Deal.stage_name)
    )

    # Stale deals (no activity > 7 days, still open)
    stale = db.execute(
        select(Deal).where(
            Deal.assigned_by == manager_name,
            Deal.last_activity_at < datetime.utcnow() - timedelta(days=7),
            Deal.is_won == False,
            Deal.is_lost == False,
        ).order_by(Deal.last_activity_at.asc()).limit(10)
    )

    # Closed deals in period (for summary)
    closed = db.execute(
        select(func.count(Deal.id), func.sum(Deal.amount)).where(
            Deal.assigned_by == manager_name,
            Deal.is_won == True,
            Deal.closed_at >= period_start,
            Deal.closed_at <= period_end,
        )
    )
    closed_row = closed.one()

    return {
        "name": manager_name,
        "period": {"from": d_from.isoformat(), "to": d_to.isoformat()},
        "closed_deals": closed_row[0] or 0,
        "closed_amount": round(closed_row[1] or 0, 0),
        "rechka_history": [
            {
                "week": r.week_number,
                "score_total": r.score_total,
                "score_contact": r.score_contact,
                "score_needs": r.score_needs,
                "score_pain": r.score_pain,
                "score_presentation": r.score_presentation,
                "score_objections": r.score_objections,
                "score_proposal": r.score_proposal,
                "score_mop_leader": r.score_mop_leader,
            }
            for r in reversed(list(history))
        ],
        "deals_by_stage": [
            {"stage": s.stage_name, "count": s.count, "total": round(s.total or 0, 0)}
            for s in deals_by_stage.all()
        ],
        "stale_deals": [
            {
                "id": d.id,
                "title": d.title,
                "amount": d.amount,
                "stage": d.stage_name,
                "days_stale": (datetime.utcnow() - d.last_activity_at).days if d.last_activity_at else None,
                "last_activity": d.last_activity_at.isoformat() if d.last_activity_at else None,
            }
            for d in stale.scalars().all()
        ],
    }


@router.get("/people/installers")
def get_installers(
    date_from: str = Query(None),
    date_to: str = Query(None),
    db: Session = Depends(get_db),
):
    """Installer workload and performance."""
    today = date.today()
    d_from = parse_date(date_from)
    d_to = parse_date(date_to)

    # If dates provided, use them; otherwise default to current week
    if d_from and d_to:
        week_start = d_from
        week_end = d_to
    else:
        week_start = today - timedelta(days=today.weekday())
        week_end = today + timedelta(days=(6 - today.weekday()))
    yesterday = today - timedelta(days=1)

    installers_data = []
    for installer in settings.INSTALLERS:
        # This week's visits
        week_visits = db.execute(
            select(
                Visit.visit_type,
                func.count(Visit.id).label("count"),
            ).where(
                Visit.assigned_installer == installer,
                Visit.scheduled_at >= datetime.combine(week_start, datetime.min.time()),
                Visit.scheduled_at <= datetime.combine(week_end, datetime.max.time()),
            ).group_by(Visit.visit_type)
        )
        visits_by_type = {r.visit_type: r.count for r in week_visits.all()}

        # Calculate workload (visits / 5 working days)
        total_visits = sum(visits_by_type.values())
        workload_pct = min(round(total_visits / 5 * 100, 0), 100)

        # Completed yesterday
        completed_yesterday = db.execute(
            select(func.count(Visit.id)).where(
                Visit.assigned_installer == installer,
                Visit.is_completed == True,
                func.date(Visit.completed_at) == yesterday,
            )
        )

        installers_data.append({
            "name": installer,
            "montages_week": visits_by_type.get("М", 0) + visits_by_type.get("M", 0),
            "inspections_week": visits_by_type.get("О", 0),
            "guarantees_week": visits_by_type.get("Г", 0),
            "diagnostics_week": visits_by_type.get("Диагн", 0),
            "total_visits_week": total_visits,
            "workload_percent": workload_pct,
            "completed_yesterday": completed_yesterday.scalar() or 0,
        })

    return {"installers": installers_data}
