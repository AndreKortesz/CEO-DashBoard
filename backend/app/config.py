"""
Configuration — environment variables for all data sources.
Phase 1: BITRIX24_*, ROISTAT_*
Phase 2: YANDEX_DIRECT_*, YANDEX_METRIKA_*
Phase 3: GOOGLE_SHEETS_*
Phase 4: ADESK_*, ONEC_*
Phase 5: ANTHROPIC_*
"""
import os
from functools import lru_cache


class Settings:
    # --- App ---
    APP_NAME: str = "CEO Dashboard — Mos-GSM"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production")

    # --- Database ---
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://localhost/ceo_dashboard")

    # --- Phase 1: Bitrix24 ---
    BITRIX24_WEBHOOK_URL: str = os.getenv("BITRIX24_WEBHOOK_URL", "")
    # Format: https://svyaz.bitrix24.ru/rest/{user_id}/{webhook_token}/
    # Separate webhook from TechBase AI

    # --- Phase 1: Roistat ---
    ROISTAT_API_KEY: str = os.getenv("ROISTAT_API_KEY", "")
    ROISTAT_PROJECT_ID: str = os.getenv("ROISTAT_PROJECT_ID", "37488")
    ROISTAT_VAT_MULTIPLIER: float = float(os.getenv("ROISTAT_VAT_MULTIPLIER", "1.2"))

    # --- Phase 2: Yandex Direct ---
    YANDEX_DIRECT_TOKEN_1: str = os.getenv("YANDEX_DIRECT_TOKEN_1", "")
    YANDEX_DIRECT_TOKEN_2: str = os.getenv("YANDEX_DIRECT_TOKEN_2", "")
    YANDEX_METRIKA_TOKEN: str = os.getenv("YANDEX_METRIKA_TOKEN", "")
    YANDEX_METRIKA_COUNTER: str = os.getenv("YANDEX_METRIKA_COUNTER", "")

    # --- Phase 3: Rechka AI (Google Sheets) ---
    GOOGLE_SHEETS_CREDENTIALS_JSON: str = os.getenv("GOOGLE_SHEETS_CREDENTIALS_JSON", "")
    RECHKA_SPREADSHEET_ID: str = os.getenv("RECHKA_SPREADSHEET_ID", "")

    # --- Phase 4: Adesk ---
    ADESK_WEBHOOK_SECRET: str = os.getenv("ADESK_WEBHOOK_SECRET", "")

    # --- Phase 4: 1C ---
    ONEC_ACCOUNTING_URL: str = os.getenv("ONEC_ACCOUNTING_URL", "")
    ONEC_ACCOUNTING_TOKEN: str = os.getenv("ONEC_ACCOUNTING_TOKEN", "")
    ONEC_UT_URL: str = os.getenv("ONEC_UT_URL", "")
    ONEC_UT_TOKEN: str = os.getenv("ONEC_UT_TOKEN", "")

    # --- Phase 5: Claude AI ---
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

    # --- Business rules ---
    MONTAGE_MIN_CHECK: int = int(os.getenv("MONTAGE_MIN_CHECK", "15000"))
    # Deals below this amount excluded from avg montage check

    # --- Bitrix24 funnel stage IDs (to be filled after webhook setup) ---
    # Leads statuses
    LEAD_STATUS_SUCCESS: str = os.getenv("LEAD_STATUS_SUCCESS", "CONVERTED")
    LEAD_REJECTIONS: list = [
        "НЕ КЛИЕНТ", "НЕ ДОЗВОН", "НЕУСПЕШНЫЙ ЛИД",
        "ДУБЛЬ", "ПОЧТА", "ОТЛОЖЕНО НА БУДУЩЕЕ"
    ]

    # Deals category
    DEALS_CATEGORY_ID: int = 7
    VISITS_CATEGORY_ID: int = 45

    # Directions
    DIRECTIONS: list = [
        "СКУД", "Видеонаблюдение", "Умный дом",
        "Усиление связи", "Пожарка", "Wi-Fi"
    ]

    # Team
    MANAGERS: list = [
        "Серафим Юнников", "Никита Наумов",
        "Богдан Горбунов", "Дарья Кудрявцева"
    ]
    ROP: str = "Павел Колбик"
    INSTALLERS: list = [
        "Олег", "Дима В", "Максим", "Андрей",
        "Сергей Фадин", "Алексей Романок",
        "Сергей Денисов", "Евгений Гус", "Александр Нужнов"
    ]

    # Cache TTL (seconds)
    CACHE_TTL_BITRIX: int = 300      # 5 min
    CACHE_TTL_ROISTAT: int = 600     # 10 min
    CACHE_TTL_RECHKA: int = 3600     # 1 hour
    CACHE_TTL_ADESK: int = 0         # real-time via webhooks
    CACHE_TTL_ONEC: int = 1800       # 30 min


@lru_cache()
def get_settings() -> Settings:
    return Settings()
