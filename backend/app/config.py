"""
Configuration — environment variables for all data sources.
Includes Bitrix24 UF field mapping from crm.lead.fields / crm.deal.fields.
"""
import os
from functools import lru_cache


class Settings:
    # --- App ---
    APP_NAME: str = "CEO Dashboard - Mos-GSM"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production")

    # --- Database ---
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://localhost/ceo_dashboard")

    # --- Phase 1: Bitrix24 ---
    BITRIX24_WEBHOOK_URL: str = os.getenv("BITRIX24_WEBHOOK_URL", "")

    # --- Phase 1: Roistat ---
    ROISTAT_API_KEY: str = os.getenv("ROISTAT_API_KEY", "")
    ROISTAT_PROJECT_ID: str = os.getenv("ROISTAT_PROJECT_ID", "37488")
    ROISTAT_VAT_MULTIPLIER: float = float(os.getenv("ROISTAT_VAT_MULTIPLIER", "1.2"))

    # --- Phase 2+ (fill later) ---
    YANDEX_DIRECT_TOKEN_1: str = os.getenv("YANDEX_DIRECT_TOKEN_1", "")
    YANDEX_DIRECT_TOKEN_2: str = os.getenv("YANDEX_DIRECT_TOKEN_2", "")
    YANDEX_METRIKA_TOKEN: str = os.getenv("YANDEX_METRIKA_TOKEN", "")
    YANDEX_METRIKA_COUNTER: str = os.getenv("YANDEX_METRIKA_COUNTER", "")
    GOOGLE_SHEETS_CREDENTIALS_JSON: str = os.getenv("GOOGLE_SHEETS_CREDENTIALS_JSON", "")
    RECHKA_SPREADSHEET_ID: str = os.getenv("RECHKA_SPREADSHEET_ID", "")
    ADESK_WEBHOOK_SECRET: str = os.getenv("ADESK_WEBHOOK_SECRET", "")
    ONEC_ACCOUNTING_URL: str = os.getenv("ONEC_ACCOUNTING_URL", "")
    ONEC_ACCOUNTING_TOKEN: str = os.getenv("ONEC_ACCOUNTING_TOKEN", "")
    ONEC_UT_URL: str = os.getenv("ONEC_UT_URL", "")
    ONEC_UT_TOKEN: str = os.getenv("ONEC_UT_TOKEN", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

    # --- Business rules ---
    MONTAGE_MIN_CHECK: int = int(os.getenv("MONTAGE_MIN_CHECK", "15000"))

    # --- Bitrix24 CRM structure ---
    DEALS_CATEGORY_ID: int = 7
    VISITS_CATEGORY_ID: int = 45
    LEAD_STATUS_SUCCESS: str = "CONVERTED"

    # --- Bitrix24 UF field IDs (from crm.lead.fields) ---
    # "Вид услуг" on leads — multiple enumeration
    BX_LEAD_DIRECTION_FIELD: str = "UF_CRM_1692125741676"
    BX_LEAD_DIRECTION_MAP: dict = {
        "4099": "Усиление связи",
        "4101": "Видеонаблюдение",
        "4103": "Интернет",
        "4105": "Wi-Fi",
        "4107": "Охранная система",
        "7213": "СКУД",
        "4109": "Прочее",
    }
    # "Причина отказа вкратце" on leads
    BX_LEAD_REJECTION_FIELD: str = "UF_CRM_1638272633594"
    # "Площадь, кв.м." on leads
    BX_LEAD_AREA_FIELD: str = "UF_CRM_1632425986529"

    # --- Bitrix24 UF field IDs (from crm.deal.fields) ---
    # "Тип выезда" on deals in visits funnel (cat 45) — enumeration
    BX_VISIT_TYPE_FIELD: str = "UF_CRM_1729503974803"
    BX_VISIT_TYPE_MAP: dict = {
        "5117": "О",       # Осмотр
        "5119": "М",       # Монтаж
        "5121": "Г",       # Гарантия
        "5123": "Диагн",   # Диагностика
        "5125": "О",       # Повторный осмотр
        "5127": "Прочее",
    }
    # "Осмотр произвел" — employee ID
    BX_INSPECTOR_FIELD: str = "UF_CRM_1730325890"
    # "Монтаж произвел" — employee ID
    BX_INSTALLER_FIELD: str = "UF_CRM_1730325877"
    # "Ссылка на сделку из воронки выезда" — URL linking visit to deal
    BX_VISIT_DEAL_LINK_FIELD: str = "UF_CRM_1731021501332"
    # "Причина отказа вкратце" on deals
    BX_DEAL_REJECTION_FIELD: str = "UF_CRM_61A625538BED7"
    # "Площадь, кв.м." on deals
    BX_DEAL_AREA_FIELD: str = "UF_CRM_1588092924225"
    # "Сделка-копия(тех. поле)" — boolean
    BX_DEAL_IS_COPY_FIELD: str = "UF_CRM_1738169221"
    # "Заказ в 1С"
    BX_ORDER_1C_FIELD: str = "UF_CRM_1699531043689"

    # --- Team ---
    DIRECTIONS: list = [
        "СКУД", "Видеонаблюдение", "Усиление связи",
        "Wi-Fi", "Интернет", "Охранная система", "Прочее"
    ]
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
    CACHE_TTL_BITRIX: int = 300
    CACHE_TTL_ROISTAT: int = 600


@lru_cache()
def get_settings() -> Settings:
    return Settings()
