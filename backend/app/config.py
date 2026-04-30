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
    API_TOKEN: str = os.getenv("API_TOKEN", "")  # Bearer token for API auth

    # --- Database ---
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://localhost/ceo_dashboard")

    # --- Phase 1: Bitrix24 ---
    BITRIX24_WEBHOOK_URL: str = os.getenv("BITRIX24_WEBHOOK_URL", "")

    # --- Phase 1: Roistat ---
    ROISTAT_API_KEY: str = os.getenv("ROISTAT_API_KEY", "")
    ROISTAT_PROJECT_ID: str = os.getenv("ROISTAT_PROJECT_ID", "37488")
    ROISTAT_VAT_MULTIPLIER: float = float(os.getenv("ROISTAT_VAT_MULTIPLIER", "1.0"))

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

    # Lead statuses that are rejections (STATUS_SEMANTIC_ID is not always "F" for custom statuses!)
    # These are determined by their position in the Bitrix24 kanban (red columns)
    LEAD_REJECTED_STATUSES: set = {
        "JUNK",       # Не клиент (system)
        "6",          # Не дозвон
        "10",         # Неуспешный лид
        "24",         # Дубль
        "27",         # Почта
    }

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
    # "Вид услуг" on DEALS — different field ID and enum IDs than leads!
    BX_DEAL_DIRECTION_FIELD: str = "UF_CRM_64DC6A0DC67D3"
    BX_DEAL_DIRECTION_MAP: dict = {
        "4111": "Усиление связи",      # УСС
        "4113": "Видеонаблюдение",      # СВН
        "4115": "Интернет",
        "4117": "Wi-Fi",                # Бесшовный интернет
        "4119": "Охранная система",
        "7219": "СКУД",
        "4121": "Прочее",
    }
    # "Тип выезда" on deals in visits funnel (cat 45) — enumeration
    BX_VISIT_TYPE_FIELD: str = "UF_CRM_1729503974803"
    BX_VISIT_TYPE_MAP: dict = {
        "4311": "О",       # Осмотр
        "4313": "М",       # Монтаж
        "4307": "Г",       # Гарантия
        "4309": "Диагн",   # Диагностика
        "7221": "М",       # Домонтаж (считаем как монтаж)
        "4315": "О",       # Повторный осмотр
        "4317": "Прочее",
        # Also keep old IDs from crm.lead.fields in case they appear
        "5117": "О",
        "5119": "М",
        "5121": "Г",
        "5123": "Диагн",
        "5125": "О",
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
