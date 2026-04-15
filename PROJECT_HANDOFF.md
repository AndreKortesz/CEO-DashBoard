# CEO Dashboard Mos-GSM — Полная инструкция для разработчика

> **Документ создан 15 апреля 2026**. Содержит ВСЁ что нужно знать для продолжения работы над проектом.

---

## Содержание

1. О проекте
2. Текущее состояние и что работает
3. Структура файлов
4. Критические решения (не менять!)
5. Последние изменения (ждут деплоя)
6. Дорожная карта
7. Известные баги и нюансы
8. Правила работы с проектом

---

## 1. О проекте

**CEO Dashboard** — утренний дашборд руководителя для компании **Mos-GSM** (интегратор низковольтных систем: СКУД, видеонаблюдение, умный дом, усиление связи, пожарка, Wi-Fi).

- **URL**: `https://ceo-dashboard-production-c36b.up.railway.app`
- **GitHub**: `AndreKortesz/CEO-DashBoard`
- **Stack**: FastAPI + React (Vite) + PostgreSQL, deployed на Railway
- **Swagger UI**: `/docs`

### 5 экранов:
1. **Пульс** — ключевые метрики за день/период, красные флаги, план-факт
2. **Воронка** — маркетинг (Roistat каналы), продажи (конверсии лид→осмотр→монтаж), по направлениям
3. **Люди** — карточки менеджеров (сделки, время реакции, Речка AI), монтажники (загрузка)
4. **Деньги** — placeholder (Phase 4: Adesk + 1С)
5. **Радар** — placeholder (Phase 5: AI-аналитика)

### Владелец
Андрей — генеральный директор/CEO-владелец Mos-GSM. Принимает архитектурные решения, даёт точные правки. Предпочитает light theme, итеративную разработку, точные цифры.

---

## 2. Текущее состояние (15 апреля 2026)

### Что работает ✅

**Backend:**
- Bitrix24 sync: лиды, сделки (cat 7), выезды (cat 45) — двойной запрос по DATE_CREATE + DATE_MODIFY
- Roistat sync: каналы, расходы с НДС ×1.2
- Автосинхронизация каждые 15 мин (days_back=30)
- API: `/pulse`, `/funnel/*`, `/people/*`, `/admin/*`, `/sync/*`
- Все API принимают `date_from` / `date_to` параметры (ISO формат)
- API-аутентификация Bearer token (сейчас отключена — пустой API_TOKEN)
- Auto-migrate новых колонок при старте (database.py)
- resolve_user загружает и неактивных пользователей из Битрикс24

**Frontend:**
- SPA React через FastAPI StaticFiles
- 5 экранов с навигацией
- SyncBadge (зелёный/жёлтый/красный)
- Колбик (РОП) — отдельный синий блок с разбивкой (всего/в работе/конвертировано/отказ)
- Менеджеры — таблица конверсий без РОПа
- Точные цифры в расходах маркетинга (formatExact)
- DatePicker компонент (создан, но требует деплой фикса UI.jsx — см. раздел 5)

**Данные:**
- Факт выручки **совпадает** с Битрикс24 UI (29 сделок, 870 758 руб. за апрель — проверено)
- Метрика "Выручка по сделкам" = OPPORTUNITY из Б24 (не валовый доход — тот будет после подключения 1С)

### Что НЕ работает ⚠️

- **Пикер дат НЕ отображается** — UI.jsx использовал `require()` который не работает в Vite. Фикс готов (ESM import), ожидает деплоя. Файл: `frontend/src/components/UI.jsx`
- **ID:36183** — resolve_user обновлён для inactive users, но нужен re-sync (days_back=90) чтобы имена обновились в базе
- **Горбунов** — отображается на "Люди" (1 сделка), но не на "Воронка→Продажи" (0 лидов за период — это нормально)
- **План продаж** — не установлен (РОП должен ввести через Swagger POST /api/admin/sales-plan)

---

## 3. Структура файлов

```
CEO-DashBoard/
├── ARCHITECTURE.md          ← Полная архитектурная документация (раздел 12 = логика дат!)
├── nixpacks.toml            ← Railway build: nodejs_20 + python311
├── railway.toml             ← Railway deploy: frontend build + backend start
│
├── backend/
│   └── app/
│       ├── config.py        ← Все env vars, UF fields, team lists, ROP="Павел Колбик"
│       ├── database.py      ← SQLAlchemy sync + psycopg v3, auto-migrate
│       ├── models.py        ← 11 моделей (Lead, Deal, Visit, RoistatChannel, SalesPlan, etc.)
│       ├── main.py          ← FastAPI app, middlewares, scheduler (15 min, days_back=30), SPA serving
│       ├── routers/
│       │   ├── pulse.py     ← /api/pulse — date_from/date_to, метрики за период
│       │   ├── funnel.py    ← /api/funnel/* — маркетинг, продажи, конверсии, РОП отделён
│       │   ├── people.py    ← /api/people/* — менеджеры, монтажники
│       │   ├── admin.py     ← /api/admin/* — CRUD план продаж
│       │   └── sync.py      ← /api/sync/* — ручной запуск sync
│       └── services/
│           ├── bitrix24.py  ← Bitrix24 REST API client (sync, users, stages)
│           ├── roistat.py   ← Roistat API client (channels, costs)
│           └── sync.py      ← Sync orchestrator (leads, deals, visits, roistat)
│
└── frontend/
    └── src/
        ├── App.jsx          ← DateContext provider, routes
        ├── api.js           ← API client (все endpoints с date_from/date_to)
        ├── components/
        │   ├── UI.jsx       ← MetricCard, Badge, HBar, RedFlag, NavBar, PageWrapper + DatePicker
        │   └── DatePicker.jsx ← Глобальный пикер дат (пресеты + произвольные)
        └── pages/
            ├── Pulse.jsx    ← Пульс: метрики вчера + за период + план-факт
            ├── Funnel.jsx   ← Воронка: маркетинг/продажи/направления
            ├── People.jsx   ← Люди: менеджеры/монтажники
            ├── Money.jsx    ← Деньги (placeholder)
            └── Radar.jsx    ← Радар (placeholder)
```

---

## 4. Критические решения (НЕ МЕНЯТЬ без понимания!)

### 4.1 Даты сделок — CLOSEDATE
**CLOSEDATE** = единственно правильное поле для метрик "успешных сделок за период". Совпадает с фильтром "Дата завершения" в UI Битрикс24.

- `DATE_MODIFY` — НЕ использовать (обновляется при любом изменении, завышает в 3+ раза)
- `crm.stagehistory.list` — НЕ использовать (фильтр по дате не работает в API)
- `won_at` поле в модели Deal — НЕ используется, осталось от эксперимента

**Подробная документация**: ARCHITECTURE.md, раздел 12.

### 4.2 Двойной sync сделок
`sync_deals()` делает ДВА запроса к Битрикс24:
1. По `DATE_CREATE >= date_from` — новые сделки
2. По `DATE_MODIFY >= date_from` — недавно изменённые (ловит старые сделки закрытые недавно)

Дедупликация по ID. Это обязательно — иначе потеряем сделки.

### 4.3 РОП (Колбик) отделён от менеджеров
Все лиды приходят на РОПа, он распределяет. ASSIGNED_BY_ID меняется при распределении.
- В конверсиях (`/funnel/conversions?group_by=manager`) — Колбик отдельно в `"rop"` ключе
- В таблице менеджеров — только 4 менеджера + unknown пользователи
- РОП-блок показывает: всего лидов, в работе, конвертировано, отказ

### 4.4 is_rejected для лидов
`Lead.is_rejected` = `STATUS_SEMANTIC_ID == "F"`. Покрывает ВСЕ отказные стадии: "Не клиент", "Дубль", "Почта", "Неуспешный лид", "Не дозвон". Без этого поля разбивка РОПа показывала 248 "в работе" вместо реальных 14.

### 4.5 Настройки в Битрикс24 — НЕ ТРОГАТЬ
Андрей явно сказал: не менять настройки в Битрикс24 ("Обновлять дату завершения при переходе в финальную стадию" и т.д.). Код должен работать с текущими настройками.

### 4.6 UF-поля Битрикс24
```
Направление (лиды):  UF_CRM_1692125741676
Направление (сделки): BX_DEAL_DIRECTION_FIELD (другое поле!)
Тип выезда:          UF_CRM_1729503974803
Монтажник:           UF_CRM_1730325877
Связь выезд→сделка:  UF_CRM_1731021501332
```

---

## 5. Последние изменения (ждут деплоя)

### Файл: `frontend/src/components/UI.jsx`
**Проблема**: DatePicker не отображается — использовался `require()` (CommonJS), а Vite требует ESM.
**Решение**: Заменён на `import DatePicker from './DatePicker'` и `import { useDates } from '../App'` в начале файла.

### После деплоя UI.jsx нужно:
1. Запустить sync через Swagger (days_back=90) — чтобы `is_rejected` и имена inactive users обновились
2. Проверить что пикер дат появился справа от заголовка на каждой странице
3. Проверить что при переключении периода данные перезагружаются

---

## 6. Дорожная карта

### Phase 1 — Bitrix24 + Roistat [~95% ГОТОВО]
| Задача | Статус |
|--------|--------|
| Backend + PostgreSQL + Railway | ✅ |
| Bitrix24 sync (лиды, сделки, выезды) | ✅ |
| Двойной sync сделок | ✅ |
| Roistat sync | ✅ |
| API endpoints | ✅ |
| Auto-sync 15 мин (30 дней) | ✅ |
| Frontend SPA (5 экранов) | ✅ |
| Факт = Битрикс24 (CLOSEDATE) | ✅ |
| ARCHITECTURE.md | ✅ |
| Колбик как РОП + разбивка is_rejected | ✅ |
| Точные цифры расходов | ✅ |
| resolve_user inactive users | ✅ |
| DatePicker (все экраны) + date_from/date_to API | ✅ (фикс UI.jsx ждёт деплоя) |
| Ввод плана продаж в дашборде | ⏳ сделать после OAuth |

### Phase 2 — Яндекс.Директ + Метрика [НЕ НАЧАТА]
- Подключить 2 аккаунта Яндекс.Директ
- Расходы по кампаниям → расходы по направлениям
- Яндекс.Метрика — визиты, конверсии на сайте

### Phase 3 — Rechka AI [НЕ НАЧАТА]
- Google Sheets API (gspread) → 7 навыков, оценки 0-100%
- Модели RechkaCall + RechkaWeekly уже в БД

### Phase 4 — Adesk + 1С [НЕ НАЧАТА]
- Adesk webhooks → ДДС, ОПиУ
- 1С Бухгалтерия (Фреш) → дебиторка
- 1С УТ (HTTP-сервис) → закупки, маржа
- **ВАЖНО**: переключить план-факт с "Выручка" на "Валовый доход"

### Phase 5 — AI + Radar [НЕ НАЧАТА]
- Claude API → AI-саммари на Пульсе
- Claude API → AI-аналитика на Радаре

### После Phase 5
- Bitrix24 OAuth авторизация на фронтенде (заменит API_TOKEN)
- Ввод плана продаж прямо в дашборде (модальное окно на Пульсе)

---

## 7. Известные баги и нюансы

### 7.1 `>=CLOSEDATE` в Bitrix24 API не работает
Фильтр `>=CLOSEDATE` возвращает ВСЕ записи (5236). Работает только строгое неравенство: `>CLOSEDATE=2026-03-31` и `<CLOSEDATE=2026-05-01`. В PostgreSQL проблемы нет — SQLAlchemy нормально фильтрует.

### 7.2 Auto-sync vs ручной sync
Auto-sync (15 мин) загружает за 30 дней. Для полной перезагрузки данных (новые поля, миграции) нужен ручной sync через Swagger: POST `/api/sync/run?days_back=90`.

### 7.3 Railway healthcheck
Не ставить healthcheck на аутентифицированные endpoints — это вызывает deployment failures. Healthcheck убран из `railway.toml`.

### 7.4 nixpacks.toml
Используем `nodejs_20` (без `nodePackages.npm` — вызывает конфликт!). Frontend билдится через `cd frontend && npm install && npm run build`.

### 7.5 Два-стадийный Dockerfile не используется
Вместо Docker используем nixpacks + railway.toml для билда. Это надёжнее на Railway.

### 7.6 "Неизвестно" в направлениях
335 лидов без направления — поле не заполнено в Битрикс24. Организационная проблема, не техническая.

### 7.7 Горбунов с 0 лидами
Богдан Горбунов в config.py MANAGERS, показывается на "Люди" (1 сделка), но отсутствует в конверсиях если за период у него 0 лидов. Это нормально.

---

## 8. Правила работы с проектом

### 8.1 ВСЕГДА сначала `view` файл, потом `str_replace`
Без исключений. Пропуск view приводил к критическим багам.

### 8.2 Отправлять ТОЛЬКО изменённые файлы
Не высылать весь архив если менялись 1-2 файла.

### 8.3 Название компании
Всегда **Mos-GSM** (латиницей). Никогда не Мос-ГСМ.

### 8.4 Light theme only
Андрей предпочитает только светлые темы. Не предлагать тёмные фоны.

### 8.5 Бренд
Bebas Neue font, жёлтый акцент `#F3C04D`, логотип с signal-bars.

### 8.6 Финансовые данные
- **Adesk** = primary finance source (не 1С)
- Rechka AI scores = as-is (не пересчитывать)
- Roistat costs × 1.2 для НДС
- План продаж по **валовому доходу** (не выручке)

---

## Приложение A: Переменные окружения

```
DATABASE_URL=postgresql://...
BITRIX24_WEBHOOK_URL=https://svyaz.bitrix24.ru/rest/9/TOKEN/
ROISTAT_API_KEY=...
ROISTAT_PROJECT_ID=37488
API_TOKEN=  (пустой = auth отключена)
VITE_API_TOKEN=  (пустой)
DEBUG=false
```

## Приложение B: Полезные команды

```bash
# Ручной sync (90 дней)
curl -X POST https://ceo-dashboard-production-c36b.up.railway.app/api/sync/run?days_back=90

# Установить план продаж
curl -X POST https://ceo-dashboard-production-c36b.up.railway.app/api/admin/sales-plan \
  -H "Content-Type: application/json" \
  -d '{"year": 2026, "month": 4, "plan_amount": 3000000}'

# Проверить данные
curl https://ceo-dashboard-production-c36b.up.railway.app/api/pulse
```

## Приложение C: Контекст для нового чата Claude

Скопируй в начало нового чата:

```
Я работаю над CEO Dashboard для Mos-GSM. Проект на GitHub: AndreKortesz/CEO-DashBoard. 
Stack: FastAPI + React + PostgreSQL, deployed на Railway.

Полная документация в ARCHITECTURE.md (12 разделов).
Инструкция для разработчика в PROJECT_HANDOFF.md.

Текущее состояние: Phase 1 (Bitrix24 + Roistat) готова на ~95%.
Последний нерешённый вопрос: DatePicker не отображается — нужен деплой фикса UI.jsx (ESM import вместо require).

Правила: всегда view файл перед edit. Отправлять только изменённые файлы. Light theme only.
```
