"""
Database models for CEO Dashboard.
Stores cached data from external sources + internal settings.
"""
from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Date,
    Boolean, Text, JSON, BigInteger, ForeignKey, Index
)
from sqlalchemy.orm import relationship
from app.database import Base


# ============================================================
# BITRIX24 CACHED DATA
# ============================================================

class Lead(Base):
    """Cached leads from Bitrix24 CRM."""
    __tablename__ = "leads"

    id = Column(BigInteger, primary_key=True)  # Bitrix24 lead ID
    title = Column(String(500))
    status_id = Column(String(50), index=True)
    status_name = Column(String(100))
    source_id = Column(String(50))
    source_name = Column(String(100))
    assigned_by = Column(String(100), index=True)       # Manager name
    direction = Column(String(100), index=True)          # СКУД, Видео, etc
    amount = Column(Float, default=0)
    created_at = Column(DateTime, index=True)
    closed_at = Column(DateTime, nullable=True)
    first_activity_at = Column(DateTime, nullable=True)  # For lead response time
    is_converted = Column(Boolean, default=False)
    rejection_reason = Column(String(200), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_leads_status_created", "status_id", "created_at"),
        Index("ix_leads_assigned_direction", "assigned_by", "direction"),
    )


class Deal(Base):
    """Cached deals from Bitrix24 CRM (category_id=7)."""
    __tablename__ = "deals"

    id = Column(BigInteger, primary_key=True)  # Bitrix24 deal ID
    title = Column(String(500))
    stage_id = Column(String(50), index=True)
    stage_name = Column(String(100))
    category_id = Column(Integer, default=7)
    assigned_by = Column(String(100), index=True)
    contact_name = Column(String(200))
    company_name = Column(String(200))
    direction = Column(String(100), index=True)
    amount = Column(Float, default=0)
    created_at = Column(DateTime, index=True)
    closed_at = Column(DateTime, nullable=True)
    last_activity_at = Column(DateTime, nullable=True)
    is_won = Column(Boolean, default=False)
    is_lost = Column(Boolean, default=False)
    won_at = Column(DateTime, nullable=True, index=True)  # Real date of transition to C7:WON (from stagehistory)
    loss_reason = Column(String(200), nullable=True)
    area_sqm = Column(Float, nullable=True)             # Площадь м2
    is_repeat = Column(Boolean, default=False)           # Повторная сделка
    updated_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_deals_stage_created", "stage_id", "created_at"),
        Index("ix_deals_assigned_direction", "assigned_by", "direction"),
    )


class Visit(Base):
    """Cached visits/tasks from Bitrix24 (category_id=45 — выезды)."""
    __tablename__ = "visits"

    id = Column(BigInteger, primary_key=True)  # Bitrix24 deal ID in cat 45
    title = Column(String(500))
    stage_id = Column(String(50), index=True)
    stage_name = Column(String(100))
    visit_type = Column(String(20), index=True)  # М, Г, О, Диагн
    deal_id = Column(BigInteger, nullable=True, index=True)  # Linked deal in cat 7
    assigned_installer = Column(String(100), index=True)
    assigned_manager = Column(String(100))
    address = Column(String(500))
    amount = Column(Float, default=0)
    scheduled_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    is_completed = Column(Boolean, default=False)
    is_failed = Column(Boolean, default=False)         # Осмотр не произведен
    created_at = Column(DateTime, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_visits_type_installer", "visit_type", "assigned_installer"),
    )


# ============================================================
# ROISTAT CACHED DATA
# ============================================================

class RoistatChannel(Base):
    """Daily marketing data per channel from Roistat."""
    __tablename__ = "roistat_channels"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, index=True)
    channel_name = Column(String(200), index=True)
    visits = Column(Integer, default=0)
    leads = Column(Integer, default=0)
    cost_without_vat = Column(Float, default=0)   # Raw from Roistat
    cost_with_vat = Column(Float, default=0)       # × 1.2
    cpl = Column(Float, default=0)
    conversion_rate = Column(Float, default=0)
    calls = Column(Integer, default=0)
    target_leads = Column(Integer, default=0)
    sales = Column(Integer, default=0)
    revenue = Column(Float, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_roistat_date_channel", "date", "channel_name", unique=True),
    )


# ============================================================
# RECHKA AI DATA (from Google Sheets)
# ============================================================

class RechkaCall(Base):
    """Individual call evaluation from Rechka AI."""
    __tablename__ = "rechka_calls"

    id = Column(Integer, primary_key=True, autoincrement=True)
    call_date = Column(DateTime, index=True)
    manager_name = Column(String(100), index=True)
    duration_seconds = Column(Integer, default=0)
    deal_link = Column(String(500), nullable=True)
    booked_for_inspection = Column(Boolean, default=False)

    # Scores 0-100
    score_contact = Column(Float, default=0)          # Установление контакта
    score_needs = Column(Float, default=0)             # Выявление потребностей
    score_pain = Column(Float, default=0)              # Усиление боли
    score_presentation = Column(Float, default=0)      # Презентация
    score_objections = Column(Float, default=0)        # Отработка возражений
    score_proposal = Column(Float, default=0)          # Предложение соотв. потребн.
    score_mop_leader = Column(Float, default=0)        # МОП лидер
    score_total = Column(Float, default=0)             # Сводная оценка

    summary = Column(Text, nullable=True)
    how_to_improve = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow)


class RechkaWeekly(Base):
    """Weekly aggregated Rechka scores (from Dashboard sheet)."""
    __tablename__ = "rechka_weekly"

    id = Column(Integer, primary_key=True, autoincrement=True)
    week_number = Column(Integer, index=True)
    year = Column(Integer, default=2026)
    manager_name = Column(String(100), index=True)  # or "ОТДЕЛ" for department
    total_calls = Column(Integer, default=0)

    score_contact = Column(Float, default=0)
    score_needs = Column(Float, default=0)
    score_pain = Column(Float, default=0)
    score_presentation = Column(Float, default=0)
    score_objections = Column(Float, default=0)
    score_proposal = Column(Float, default=0)
    score_mop_leader = Column(Float, default=0)
    score_total = Column(Float, default=0)

    updated_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_rechka_weekly_wk_mgr", "week_number", "year", "manager_name", unique=True),
    )


# ============================================================
# ADESK FINANCIAL DATA (via webhooks)
# ============================================================

class AdeskTransaction(Base):
    """Financial transactions from Adesk (ДДС)."""
    __tablename__ = "adesk_transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    external_id = Column(String(100), unique=True, nullable=True)
    date = Column(Date, index=True)
    account_name = Column(String(100))     # ООО / ИП / Наличные
    category = Column(String(200))          # ФОТ, Реклама, Закупки, etc
    contragent = Column(String(200), nullable=True, index=True)
    amount = Column(Float)                  # positive = income, negative = expense
    description = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow)


# ============================================================
# 1C DATA
# ============================================================

class Receivable(Base):
    """Accounts receivable from 1C Accounting (дебиторка)."""
    __tablename__ = "receivables"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contragent = Column(String(200), index=True)
    amount = Column(Float)
    due_date = Column(Date, nullable=True)
    days_overdue = Column(Integer, default=0)
    document_number = Column(String(100), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow)


class Purchase(Base):
    """Purchases from 1C UT (закупки)."""
    __tablename__ = "purchases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_number = Column(String(100))
    contragent = Column(String(200), index=True)     # Client name (for matching)
    supplier = Column(String(200))
    items_description = Column(Text)
    amount = Column(Float)
    date = Column(Date, index=True)
    status = Column(String(50))                       # ordered, in_transit, delivered
    deal_id = Column(BigInteger, nullable=True)       # Matched Bitrix24 deal
    prepayment_amount = Column(Float, default=0)      # From Adesk
    frozen_capital = Column(Float, default=0)          # amount - prepayment
    expected_roi_date = Column(Date, nullable=True)    # Montage date
    is_stock = Column(Boolean, default=False)          # No client order = stock
    updated_at = Column(DateTime, default=datetime.utcnow)


# ============================================================
# INTERNAL SETTINGS
# ============================================================

class SalesPlan(Base):
    """Monthly sales plan (валовый доход) set by РОП."""
    __tablename__ = "sales_plans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    year = Column(Integer, index=True)
    month = Column(Integer, index=True)
    plan_amount = Column(Float)                 # Валовый доход plan
    created_by = Column(String(100))            # РОП name
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_sales_plan_ym", "year", "month", unique=True),
    )


class DashboardSnapshot(Base):
    """Daily snapshot for historical trends."""
    __tablename__ = "dashboard_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, unique=True, index=True)
    data = Column(JSON)  # Full pulse data as JSON
    created_at = Column(DateTime, default=datetime.utcnow)
