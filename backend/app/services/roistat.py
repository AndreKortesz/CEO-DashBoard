"""
Roistat API client (SYNC).
Fetches marketing analytics: channels, costs, leads, ROI.
Costs multiplied by VAT_MULTIPLIER (1.2) for real spend.
"""
import httpx
from datetime import date, timedelta
from app.config import get_settings

settings = get_settings()
ROISTAT_API_BASE = "https://cloud.roistat.com/api/v1"


class RoistatService:
    """Synchronous client for Roistat Analytics API."""

    def __init__(self):
        self.api_key = settings.ROISTAT_API_KEY
        self.project_id = settings.ROISTAT_PROJECT_ID
        self.vat_mult = settings.ROISTAT_VAT_MULTIPLIER
        self.client = httpx.Client(timeout=30.0)

    def _call(self, endpoint: str, payload: dict = None) -> dict:
        url = f"{ROISTAT_API_BASE}/{endpoint}"
        params = {"project": self.project_id}
        response = self.client.post(
            url, json=payload or {},
            headers={"Content-Type": "application/json", "Api-key": self.api_key},
            params=params,
        )
        response.raise_for_status()
        return response.json()

    def get_channel_summary(
        self,
        date_from: date = None,
        date_to: date = None,
    ) -> list:
        """Get summary per marketing channel with VAT-adjusted costs."""
        if not date_from:
            date_from = date.today().replace(day=1)
        if not date_to:
            date_to = date.today()

        data = self._call("project/analytics/data", {
            "period": {
                "from": f"{date_from.isoformat()}T00:00:00+0300",
                "to": f"{date_to.isoformat()}T23:59:59+0300",
            },
            "dimensions": ["marker_level_1"],
            "metrics": [
                "visitCount", "visits2leads", "leadCount",
                "callCount", "costPerLead", "saleCount",
                "salesAmount", "cost",
            ],
        })

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
            conv = round(leads / visits * 100, 2) if visits > 0 else 0
            roi = round((revenue - cost_with_vat) / cost_with_vat * 100, 1) if cost_with_vat > 0 else None

            channels.append({
                "channel_name": item.get("title", "Unknown"),
                "visits": visits,
                "leads": leads,
                "calls": calls,
                "cost_without_vat": cost_raw,
                "cost_with_vat": cost_with_vat,
                "cpl": cpl,
                "conversion_rate": conv,
                "sales": sales,
                "revenue": revenue,
                "roi": roi,
            })

        channels.sort(key=lambda x: x["leads"], reverse=True)
        return channels


# Singleton
roistat_service = RoistatService()
