"""
Bitrix24 REST API client.
Handles leads (crm.lead.*), deals (crm.deal.*, category_id=7),
and visits (crm.deal.*, category_id=45).
"""
import httpx
from datetime import datetime, timedelta
from typing import Optional
from app.config import get_settings

settings = get_settings()


class Bitrix24Service:
    """Client for Bitrix24 REST API via webhook."""

    def __init__(self):
        self.base_url = settings.BITRIX24_WEBHOOK_URL.rstrip("/")
        self.client = httpx.AsyncClient(timeout=30.0)

    async def _call(self, method: str, params: dict = None) -> dict:
        """Make a single API call."""
        url = f"{self.base_url}/{method}"
        response = await self.client.post(url, json=params or {})
        response.raise_for_status()
        return response.json()

    async def _fetch_all(self, method: str, params: dict = None) -> list:
        """Fetch all records with pagination (50 per page)."""
        params = params or {}
        all_items = []
        start = 0

        while True:
            params["start"] = start
            data = await self._call(method, params)
            items = data.get("result", [])

            if isinstance(items, dict):
                # Some methods return dict with nested results
                items = list(items.values()) if items else []

            all_items.extend(items)

            next_start = data.get("next")
            if not next_start or len(items) == 0:
                break
            start = next_start

        return all_items

    # =========================================================
    # LEADS
    # =========================================================

    async def get_leads(
        self,
        status_id: str = None,
        assigned_by: int = None,
        date_from: datetime = None,
        date_to: datetime = None,
    ) -> list:
        """Fetch leads with optional filters."""
        filters = {}
        if status_id:
            filters["STATUS_ID"] = status_id
        if assigned_by:
            filters["ASSIGNED_BY_ID"] = assigned_by
        if date_from:
            filters[">=DATE_CREATE"] = date_from.isoformat()
        if date_to:
            filters["<=DATE_CREATE"] = date_to.isoformat()

        params = {
            "filter": filters,
            "select": [
                "ID", "TITLE", "STATUS_ID", "SOURCE_ID", "SOURCE_DESCRIPTION",
                "ASSIGNED_BY_ID", "OPPORTUNITY", "DATE_CREATE", "DATE_CLOSED",
                "UF_*",  # Custom fields including направление
            ],
            "order": {"DATE_CREATE": "DESC"},
        }
        return await self._fetch_all("crm.lead.list", params)

    async def get_lead_statuses(self) -> list:
        """Get all lead status names."""
        data = await self._call("crm.status.list", {
            "filter": {"ENTITY_ID": "STATUS"}
        })
        return data.get("result", [])

    async def get_lead_activities(self, lead_id: int) -> list:
        """Get activities for a lead (for response time calculation)."""
        data = await self._call("crm.activity.list", {
            "filter": {
                "OWNER_TYPE_ID": 1,  # Lead
                "OWNER_ID": lead_id,
            },
            "order": {"CREATED": "ASC"},
            "select": ["ID", "CREATED", "TYPE_ID", "DIRECTION"],
        })
        return data.get("result", [])

    # =========================================================
    # DEALS (category_id=7 — main sales funnel)
    # =========================================================

    async def get_deals(
        self,
        stage_id: str = None,
        assigned_by: int = None,
        category_id: int = 7,
        date_from: datetime = None,
    ) -> list:
        """Fetch deals from specified category."""
        filters = {"CATEGORY_ID": category_id}
        if stage_id:
            filters["STAGE_ID"] = stage_id
        if assigned_by:
            filters["ASSIGNED_BY_ID"] = assigned_by
        if date_from:
            filters[">=DATE_CREATE"] = date_from.isoformat()

        params = {
            "filter": filters,
            "select": [
                "ID", "TITLE", "STAGE_ID", "CATEGORY_ID",
                "ASSIGNED_BY_ID", "CONTACT_ID", "COMPANY_ID",
                "OPPORTUNITY", "DATE_CREATE", "CLOSEDATE",
                "DATE_MODIFY", "UF_*",
            ],
            "order": {"DATE_CREATE": "DESC"},
        }
        return await self._fetch_all("crm.deal.list", params)

    async def get_deal_stages(self, category_id: int = 7) -> list:
        """Get deal stage names for a category."""
        data = await self._call("crm.dealcategory.stage.list", {
            "id": category_id
        })
        return data.get("result", [])

    async def get_stale_deals(self, days: int = 7, category_id: int = 7) -> list:
        """Get deals with no activity for N days."""
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        params = {
            "filter": {
                "CATEGORY_ID": category_id,
                "<=DATE_MODIFY": cutoff,
                "!STAGE_SEMANTIC_ID": "S",  # Exclude won
            },
            "select": [
                "ID", "TITLE", "STAGE_ID", "ASSIGNED_BY_ID",
                "OPPORTUNITY", "DATE_MODIFY", "UF_*",
            ],
            "order": {"DATE_MODIFY": "ASC"},
        }
        return await self._fetch_all("crm.deal.list", params)

    # =========================================================
    # VISITS (category_id=45 — выезды)
    # =========================================================

    async def get_visits(
        self,
        stage_id: str = None,
        date_from: datetime = None,
    ) -> list:
        """Fetch visits/inspections/montages."""
        return await self.get_deals(
            stage_id=stage_id,
            category_id=settings.VISITS_CATEGORY_ID,
            date_from=date_from,
        )

    # =========================================================
    # TASKS (for overdue tracking)
    # =========================================================

    async def get_overdue_tasks(self, responsible_id: int = None) -> list:
        """Get overdue tasks."""
        filters = {
            "<=DEADLINE": datetime.utcnow().isoformat(),
            "!STATUS": [4, 5, 6, 7],  # Not completed/deferred
        }
        if responsible_id:
            filters["RESPONSIBLE_ID"] = responsible_id

        params = {
            "filter": filters,
            "select": [
                "ID", "TITLE", "RESPONSIBLE_ID", "DEADLINE",
                "STATUS", "GROUP_ID", "UF_CRM_TASK",
            ],
            "order": {"DEADLINE": "ASC"},
        }
        return await self._fetch_all("tasks.task.list", params)

    # =========================================================
    # USERS (for mapping IDs to names)
    # =========================================================

    async def get_users(self) -> list:
        """Get all active users."""
        data = await self._call("user.get", {
            "filter": {"ACTIVE": True},
        })
        return data.get("result", [])

    async def get_user_map(self) -> dict:
        """Get mapping: user_id -> full_name."""
        users = await self.get_users()
        return {
            u["ID"]: f"{u.get('NAME', '')} {u.get('LAST_NAME', '')}".strip()
            for u in users
        }

    # =========================================================
    # CALLS (for call count per manager)
    # =========================================================

    async def get_calls(
        self,
        date_from: datetime = None,
        date_to: datetime = None,
    ) -> list:
        """Get call activities."""
        filters = {"TYPE_ID": 2}  # Calls
        if date_from:
            filters[">=CREATED"] = date_from.isoformat()
        if date_to:
            filters["<=CREATED"] = date_to.isoformat()

        params = {
            "filter": filters,
            "select": ["ID", "RESPONSIBLE_ID", "CREATED", "DIRECTION"],
        }
        return await self._fetch_all("crm.activity.list", params)


# Singleton
bitrix24_service = Bitrix24Service()
