"""
Roistat API client.
Fetches marketing analytics: channels, costs, leads, ROI.
Costs are multiplied by VAT_MULTIPLIER (1.2) for real spend.
"""
import httpx
from datetime import date, timedelta
from app.config import get_settings

settings = get_settings()

ROISTAT_API_BASE = "https://cloud.roistat.com/api/v1"


class RoistatService:
    """Client for Roistat Analytics API."""

    def __init__(self):
        self.api_key = settings.ROISTAT_API_KEY
        self.project_id = settings.ROISTAT_PROJECT_ID
        self.vat_mult = settings.ROISTAT_VAT_MULTIPLIER
        self.client = httpx.AsyncClient(timeout=30.0)

    def _headers(self) -> dict:
        return {
            "Content-Type": "application/json",
            "Api-key": self.api_key,
        }

    async def _call(self, endpoint: str, payload: dict = None) -> dict:
        """Make API call to Roistat."""
        url = f"{ROISTAT_API_BASE}/{endpoint}"
        params = {"project": self.project_id}
        response = await self.client.post(
            url, json=payload or {}, headers=self._headers(), params=params
        )
        response.raise_for_status()
        return response.json()

    async def get_analytics(
        self,
        date_from: date,
        date_to: date,
        dimensions: list = None,
        metrics: list = None,
    ) -> dict:
        """
        Fetch analytics data.
        Default: channel-level metrics.
        """
        payload = {
            "from": date_from.isoformat(),
            "to": date_to.isoformat(),
            "dimensions": dimensions or ["marker_level_1"],
            "metrics": metrics or [
                "visitCount",
                "visits2leads",
                "leadCount",
                "callCount",
                "costPerLead",
                "costPerOrder",
                "saleCount",
                "salesAmount",
                "cost",
            ],
            "period": "day",
        }
        return await self._call("project/analytics/data", payload)

    async def get_channel_summary(
        self,
        date_from: date = None,
        date_to: date = None,
    ) -> list:
        """
        Get summary per marketing channel.
        Returns list of dicts with channel metrics.
        Costs include VAT multiplier.
        """
        if not date_from:
            date_from = date.today().replace(day=1)
        if not date_to:
            date_to = date.today()

        data = await self.get_analytics(date_from, date_to)

        channels = []
        for item in data.get("data", []):
            cost_raw = float(item.get("cost", 0) or 0)
            leads = int(item.get("leadCount", 0) or 0)
            visits = int(item.get("visitCount", 0) or 0)
            sales = int(item.get("saleCount", 0) or 0)
            revenue = float(item.get("salesAmount", 0) or 0)
            calls = int(item.get("callCount", 0) or 0)

            cost_with_vat = round(cost_raw * self.vat_mult, 2)
            cpl = round(cost_with_vat / leads, 2) if leads > 0 else 0
            conv_rate = round(leads / visits * 100, 2) if visits > 0 else 0
            roi = round((revenue - cost_with_vat) / cost_with_vat * 100, 1) if cost_with_vat > 0 else None

            channels.append({
                "channel_name": item.get("title", item.get("marker_level_1", "Unknown")),
                "visits": visits,
                "leads": leads,
                "calls": calls,
                "cost_without_vat": cost_raw,
                "cost_with_vat": cost_with_vat,
                "cpl": cpl,
                "conversion_rate": conv_rate,
                "sales": sales,
                "revenue": revenue,
                "roi": roi,
            })

        # Sort by leads descending
        channels.sort(key=lambda x: x["leads"], reverse=True)
        return channels

    async def get_daily_costs(
        self,
        date_from: date = None,
        date_to: date = None,
    ) -> list:
        """Get daily total ad spend (with VAT)."""
        if not date_from:
            date_from = date.today() - timedelta(days=30)
        if not date_to:
            date_to = date.today()

        data = await self.get_analytics(
            date_from, date_to,
            dimensions=["date"],
            metrics=["cost", "leadCount"],
        )

        daily = []
        for item in data.get("data", []):
            cost_raw = float(item.get("cost", 0) or 0)
            daily.append({
                "date": item.get("date", item.get("title", "")),
                "cost_with_vat": round(cost_raw * self.vat_mult, 2),
                "leads": int(item.get("leadCount", 0) or 0),
            })
        return daily


# Singleton
roistat_service = RoistatService()
