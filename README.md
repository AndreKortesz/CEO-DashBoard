# CEO Dashboard — Mos-GSM

Утренний CEO-дашборд для компании Mos-GSM (низковольтные системы: СКУД, видеонаблюдение, умный дом).

## Архитектура

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   React SPA  │────▶│  FastAPI      │────▶│  PostgreSQL   │
│   (frontend) │     │  (backend)    │     │  (Railway)    │
└──────────────┘     └──────┬───────┘     └──────────────┘
                           │
                    ┌──────┴───────┐
                    │  Data Sources │
                    ├──────────────┤
                    │ Bitrix24 API │  ◀── Phase 1
                    │ Roistat API  │  ◀── Phase 1
                    │ Yandex Direct│  ◀── Phase 2
                    │ Yandex Metrik│  ◀── Phase 2
                    │ Google Sheets│  ◀── Phase 3 (Rechka AI)
                    │ Adesk webhooks│ ◀── Phase 4
                    │ 1C Accounting│  ◀── Phase 4
                    │ 1C UT        │  ◀── Phase 4
                    │ Claude API   │  ◀── Phase 5
                    └──────────────┘
```

## Стек

- **Backend:** FastAPI (Python 3.11+)
- **Frontend:** React 18 + Tailwind CSS
- **Database:** PostgreSQL 15
- **Deployment:** Railway (GitHub auto-deploy)
- **Auth:** Bitrix24 OAuth (svyaz.bitrix24.ru)

## Экраны

1. **Пульс** — 8 ключевых метрик, красные флаги, AI-саммари
2. **Воронка** — маркетинг (Roistat), продажи (Bitrix24), конверсии по направлениям
3. **Люди** — менеджеры (Bitrix24 + Rechka AI), монтажники (Bitrix24 выезды)
4. **Деньги** — ДДС (Adesk), дебиторка (1С Бух), закупки (1С УТ)
5. **Радар** — риски, прогнозы, AI-аналитика (Claude API)

## Структура проекта

```
ceo-dashboard/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, CORS, routes
│   │   ├── config.py            # Environment variables
│   │   ├── database.py          # PostgreSQL connection
│   │   ├── models.py            # SQLAlchemy models
│   │   ├── services/
│   │   │   ├── bitrix24.py      # Bitrix24 API client
│   │   │   ├── roistat.py       # Roistat API client
│   │   │   ├── rechka.py        # Google Sheets (Rechka AI)
│   │   │   ├── adesk.py         # Adesk webhooks
│   │   │   ├── onec.py          # 1C HTTP services client
│   │   │   └── ai_summary.py    # Claude API for AI insights
│   │   ├── routers/
│   │   │   ├── pulse.py         # /api/pulse
│   │   │   ├── funnel.py        # /api/funnel
│   │   │   ├── people.py        # /api/people
│   │   │   ├── money.py         # /api/money
│   │   │   ├── radar.py         # /api/radar
│   │   │   └── admin.py         # /api/admin (sales plan, settings)
│   │   └── utils/
│   │       ├── conversions.py   # Funnel conversion calculations
│   │       └── cache.py         # Redis/in-memory cache
│   ├── requirements.txt
│   └── Procfile
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── pages/
│   │   │   ├── Pulse.jsx
│   │   │   ├── Funnel.jsx
│   │   │   ├── People.jsx
│   │   │   ├── Money.jsx
│   │   │   └── Radar.jsx
│   │   └── components/
│   ├── package.json
│   └── tailwind.config.js
├── .github/
│   └── workflows/
│       └── deploy.yml
├── railway.toml
└── README.md
```

## Фазы разработки

### Phase 1 — Bitrix24 + Roistat (70% ценности)
- [ ] Backend: Bitrix24 API client (leads, deals, tasks)
- [ ] Backend: Roistat API client (channels, costs, leads)
- [ ] Database: models for cached data
- [ ] API: /pulse, /funnel, /people endpoints
- [ ] Frontend: Pulse, Funnel, People screens

### Phase 2 — Yandex Direct + Metrika
### Phase 3 — Rechka AI (Google Sheets)
### Phase 4 — Adesk + 1C
### Phase 5 — AI Summary + Radar
