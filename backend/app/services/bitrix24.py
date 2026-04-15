"""
Bitrix24 REST API client (SYNC).
Handles leads, deals (cat 7), visits (cat 45), users, stages.
All methods are synchronous — compatible with sync SQLAlchemy routers.
"""
import httpx
import time
from datetime import datetime, timedelta
from app.config import get_settings

settings = get_settings()


class Bitrix24Service:
    """Synchronous client for Bitrix24 REST API via webhook."""

    def __init__(self):
        self.base_url = settings.BITRIX24_WEBHOOK_URL.rstrip("/")
        self.client = httpx.Client(timeout=30.0)
        self._user_map = None
        self._stage_maps = {}

    def _call(self, method: str, params: dict = None) -> dict:
        url = f"{self.base_url}/{method}"
        response = self.client.post(url, json=params or {})
        response.raise_for_status()
        return response.json()

    def _fetch_all(self, method: str, params: dict = None) -> list:
        """Fetch all records with pagination (50 per page). Respects rate limits."""
        params = params or {}
        all_items = []
        start = 0

        while True:
            params["start"] = start
            data = self._call(method, params)
            result = data.get("result", [])

            # tasks.task.list returns {"tasks": [...]}
            if isinstance(result, dict):
                if "tasks" in result:
                    items = result["tasks"]
                else:
                    items = list(result.values()) if result else []
            else:
                items = result

            all_items.extend(items)

            next_start = data.get("next")
            if not next_start or len(items) == 0:
                break
            start = next_start

            # Rate limit: Bitrix24 allows 2 req/sec for webhooks
            time.sleep(0.5)

        return all_items

    # =========================================================
    # USER MAP (ID -> full name)
    # =========================================================

    def get_user_map(self) -> dict:
        """Get mapping: user_id (str) -> full name. Cached per instance."""
        if self._user_map is not None:
            return self._user_map

        # Load active users
        users = self._call("user.get", {"filter": {"ACTIVE": True}})
        result = users.get("result", [])
        self._user_map = {}
        for u in result:
            uid = str(u.get("ID", ""))
            name = f"{u.get('NAME', '')} {u.get('LAST_NAME', '')}".strip()
            if uid and name:
                self._user_map[uid] = name

        # Also load inactive users (fired/deactivated)
        try:
            inactive = self._call("user.get", {"filter": {"ACTIVE": False}})
            for u in inactive.get("result", []):
                uid = str(u.get("ID", ""))
                name = f"{u.get('NAME', '')} {u.get('LAST_NAME', '')}".strip()
                if uid and name and uid not in self._user_map:
                    self._user_map[uid] = name
        except Exception:
            pass  # Non-critical — active users are enough

        return self._user_map

    def resolve_user(self, user_id) -> str:
        """Resolve user ID to name. Falls back to direct API lookup."""
        if not user_id:
            return ""
        uid = str(user_id)
        name = self.get_user_map().get(uid)
        if name:
            return name
        # Direct lookup for users not in cache (bots, external, etc.)
        try:
            resp = self._call("user.get", {"ID": uid})
            users = resp.get("result", [])
            if users:
                u = users[0]
                resolved = f"{u.get('NAME', '')} {u.get('LAST_NAME', '')}".strip()
                if resolved:
                    self._user_map[uid] = resolved
                    return resolved
        except Exception:
            pass
        return f"ID:{user_id}"

    # =========================================================
    # STAGE MAP (stage_id -> stage name)
    # =========================================================

    def get_stage_map(self, category_id: int) -> dict:
        """Get stage_id -> stage_name for a deal category. Cached."""
        if category_id in self._stage_maps:
            return self._stage_maps[category_id]

        data = self._call("crm.dealcategory.stage.list", {"id": category_id})
        stages = data.get("result", [])
        self._stage_maps[category_id] = {
            s["STATUS_ID"]: s["NAME"] for s in stages
        }
        return self._stage_maps[category_id]

    def get_lead_status_map(self) -> dict:
        """Get lead status_id -> status_name."""
        data = self._call("crm.status.list", {"filter": {"ENTITY_ID": "STATUS"}})
        return {s["STATUS_ID"]: s["NAME"] for s in data.get("result", [])}

    # =========================================================
    # LEADS
    # =========================================================

    def get_leads(self, date_from: datetime = None, date_to: datetime = None) -> list:
        filters = {}
        if date_from:
            filters[">=DATE_CREATE"] = date_from.isoformat()
        if date_to:
            filters["<=DATE_CREATE"] = date_to.isoformat()

        return self._fetch_all("crm.lead.list", {
            "filter": filters,
            "select": [
                "ID", "TITLE", "STATUS_ID", "SOURCE_ID",
                "ASSIGNED_BY_ID", "OPPORTUNITY", "DATE_CREATE",
                "DATE_CLOSED", "DATE_MODIFY", "STATUS_SEMANTIC_ID",
                "LAST_ACTIVITY_TIME",
                settings.BX_LEAD_DIRECTION_FIELD,
                settings.BX_LEAD_REJECTION_FIELD,
                settings.BX_LEAD_AREA_FIELD,
            ],
            "order": {"ID": "ASC"},
        })

    # =========================================================
    # DEALS (category_id=7 — main sales funnel)
    # =========================================================

    def get_deals(self, category_id: int = 7, date_from: datetime = None, date_modify_from: datetime = None) -> list:
        filters = {"CATEGORY_ID": category_id}
        if date_modify_from:
            filters[">=DATE_MODIFY"] = date_modify_from.isoformat()
        elif date_from:
            filters[">=DATE_CREATE"] = date_from.isoformat()

        return self._fetch_all("crm.deal.list", {
            "filter": filters,
            "select": [
                "ID", "TITLE", "STAGE_ID", "CATEGORY_ID",
                "ASSIGNED_BY_ID", "CONTACT_ID", "COMPANY_ID",
                "OPPORTUNITY", "DATE_CREATE", "CLOSEDATE",
                "DATE_MODIFY", "STAGE_SEMANTIC_ID",
                settings.BX_DEAL_DIRECTION_FIELD,
                settings.BX_DEAL_REJECTION_FIELD,
                settings.BX_DEAL_AREA_FIELD,
                settings.BX_DEAL_IS_COPY_FIELD,
                settings.BX_ORDER_1C_FIELD,
            ],
            "order": {"ID": "ASC"},
        })

    # =========================================================
    # VISITS (category_id=45 — выезды)
    # =========================================================

    def get_visits(self, date_from: datetime = None) -> list:
        filters = {"CATEGORY_ID": settings.VISITS_CATEGORY_ID}
        if date_from:
            filters[">=DATE_CREATE"] = date_from.isoformat()

        return self._fetch_all("crm.deal.list", {
            "filter": filters,
            "select": [
                "ID", "TITLE", "STAGE_ID", "CATEGORY_ID",
                "ASSIGNED_BY_ID", "OPPORTUNITY",
                "DATE_CREATE", "CLOSEDATE", "DATE_MODIFY",
                "STAGE_SEMANTIC_ID",
                settings.BX_VISIT_TYPE_FIELD,
                settings.BX_INSPECTOR_FIELD,
                settings.BX_INSTALLER_FIELD,
                settings.BX_VISIT_DEAL_LINK_FIELD,
            ],
            "order": {"ID": "ASC"},
        })

    # =========================================================
    # STAGE HISTORY — real date of transition to WON
    # =========================================================

    def get_won_dates(self, category_id: int = 7, date_from: datetime = None) -> dict:
        """
        Get mapping: deal_id -> won_at datetime.
        Uses crm.stagehistory.list to find exact date when deal moved to C{cat}:WON.
        Returns dict {deal_id: datetime}.
        """
        stage_won = f"C{category_id}:WON"
        params = {
            "entityTypeId": 2,
            "order": {"ID": "DESC"},
            "filter": {"STAGE_ID": stage_won},
            "select": ["OWNER_ID", "CREATED_TIME"],
        }

        all_items = []
        start = 0

        while True:
            params["start"] = start
            data = self._call("crm.stagehistory.list", params)
            items = data.get("result", {}).get("items", [])
            if not items:
                break

            # Check if we've gone past our date_from cutoff
            if date_from:
                oldest_in_page = items[-1].get("CREATED_TIME", "")
                try:
                    oldest_dt = datetime.fromisoformat(
                        oldest_in_page.replace("T", " ").split("+")[0]
                    )
                    if oldest_dt < date_from:
                        # Keep only items within range and stop
                        for item in items:
                            ct = item.get("CREATED_TIME", "")
                            try:
                                dt = datetime.fromisoformat(ct.replace("T", " ").split("+")[0])
                                if dt >= date_from:
                                    all_items.append(item)
                            except (ValueError, TypeError):
                                pass
                        break
                except (ValueError, TypeError):
                    pass

            all_items.extend(items)

            next_start = data.get("next")
            if not next_start:
                break
            start = next_start
            time.sleep(0.5)

        # Build mapping: deal_id -> won_at (take LAST transition to WON per deal)
        won_map = {}
        for item in all_items:
            deal_id = int(item.get("OWNER_ID", 0))
            ct = item.get("CREATED_TIME", "")
            if not deal_id or not ct:
                continue
            try:
                dt = datetime.fromisoformat(ct.replace("T", " ").split("+")[0])
            except (ValueError, TypeError):
                continue
            # Keep the most recent WON transition
            if deal_id not in won_map or dt > won_map[deal_id]:
                won_map[deal_id] = dt

        print(f"[BX24] Stage history: {len(won_map)} deals with WON date (stage={stage_won})")
        return won_map

    # =========================================================
    # LEAD ACTIVITIES (for response time)
    # =========================================================

    def get_first_activity_time(self, lead_id: int) -> datetime | None:
        """Get the time of the first activity on a lead."""
        data = self._call("crm.activity.list", {
            "filter": {
                "OWNER_TYPE_ID": 1,
                "OWNER_ID": lead_id,
            },
            "order": {"CREATED": "ASC"},
            "select": ["ID", "CREATED"],
        })
        activities = data.get("result", [])
        if activities:
            try:
                return datetime.fromisoformat(
                    activities[0]["CREATED"].replace("+03:00", "").replace("T", " ").split("+")[0]
                )
            except (KeyError, ValueError, IndexError):
                pass
        return None


# Singleton
bitrix24_service = Bitrix24Service()
