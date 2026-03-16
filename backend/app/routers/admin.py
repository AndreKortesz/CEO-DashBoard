"""
/api/admin — Admin panel for settings.
Sales plan, thresholds, manual overrides.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import SalesPlan

router = APIRouter()


class SalesPlanInput(BaseModel):
    year: int
    month: int
    plan_amount: float
    created_by: str = "РОП"


@router.get("/sales-plan")
async def get_sales_plans(
    year: int = None,
    db: AsyncSession = Depends(get_db),
):
    """Get all sales plans, optionally filtered by year."""
    query = select(SalesPlan)
    if year:
        query = query.where(SalesPlan.year == year)
    query = query.order_by(SalesPlan.year, SalesPlan.month)

    result = await db.execute(query)
    plans = result.scalars().all()

    return [
        {
            "year": p.year,
            "month": p.month,
            "plan_amount": p.plan_amount,
            "created_by": p.created_by,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in plans
    ]


@router.post("/sales-plan")
async def set_sales_plan(
    plan: SalesPlanInput,
    db: AsyncSession = Depends(get_db),
):
    """Set or update monthly sales plan (валовый доход)."""
    if plan.month < 1 or plan.month > 12:
        raise HTTPException(status_code=400, detail="Month must be 1-12")
    if plan.plan_amount <= 0:
        raise HTTPException(status_code=400, detail="Plan amount must be positive")

    # Check if exists
    existing = await db.execute(
        select(SalesPlan).where(
            SalesPlan.year == plan.year,
            SalesPlan.month == plan.month,
        )
    )
    row = existing.scalar_one_or_none()

    if row:
        row.plan_amount = plan.plan_amount
        row.created_by = plan.created_by
        row.created_at = datetime.utcnow()
    else:
        row = SalesPlan(
            year=plan.year,
            month=plan.month,
            plan_amount=plan.plan_amount,
            created_by=plan.created_by,
        )
        db.add(row)

    await db.commit()

    return {
        "status": "ok",
        "year": plan.year,
        "month": plan.month,
        "plan_amount": plan.plan_amount,
    }
