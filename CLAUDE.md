# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally (from project root)
uvicorn main:app --reload

# Run in production (Render)
uvicorn main:app --host 0.0.0.0 --port $PORT

# Trigger a manual rate fetch (no scheduler needed)
curl -X POST http://localhost:8000/rates/fetch

# Interactive API docs
open http://localhost:8000/docs
```

**Environment variables** (see `.env.example`):

| Variable | Default | Purpose |
|---|---|---|
| `SENDGRID_API_KEY` | — | Required for email delivery |
| `SENDER_EMAIL` | — | From-address for all emails |
| `FETCH_INTERVAL_MINUTES` | `60` | Scheduler cadence |
| `ALERT_COOLDOWN_HOURS` | `4` | Minimum gap between repeated alerts |

Email features degrade gracefully when `SENDGRID_API_KEY` / `SENDER_EMAIL` are absent (logged warning, no crash).

## Architecture

The app follows **MVC + Repository pattern** with SOLID applied at every layer. The flow is strictly one-directional:

```
HTTP request
    │
    ▼
Controllers  (app/controllers/)       — parse HTTP, validate, call service, return schema
    │
    ▼
Services     (app/models/services/)   — business logic only, call repositories
    │
    ▼
Repositories (app/models/repositories/) — all DB queries, return ORM objects
    │
    ▼
ORM Models   (app/models/)            — SQLAlchemy table definitions, pure data
```

**Views** live in `app/views/`:
- `schemas/` — Pydantic models for request/response serialization (no logic)
- `templates/` — HTML rendered server-side (`landing.py` returns the dashboard)

**Core** (`app/core/`) wires infrastructure:
- `config.py` — reads env vars, exposes constants
- `database.py` — SQLite engine, `SessionLocal`, `Base`, and `get_db()` FastAPI dependency
- `scheduler.py` — APScheduler background job that calls `RateService → AlertService → ReportService` on each tick

**Composition root** is `app/main.py`: creates the FastAPI app, registers all routers, mounts static files, and starts/stops the scheduler via `lifespan`.

`main.py` at the project root is a thin re-export (`from app.main import app`) required by uvicorn's start command.

## Key design rules

- **Controllers never touch repositories directly.** All DB access goes through a service.
- **Services never import other services** (except `AlertService` and `ReportService` both use `EmailService`, which is a pure utility, not a domain service).
- **Repositories never contain business logic** — only query construction and commit/refresh.
- **ORM models are never imported into controllers or schemas** — they only cross the service→repository boundary.
- **`EmailService` is stateless** — `send()` is a static method; it reads config at call time so it degrades silently if credentials are missing.

## Adding a new rate source

1. Add a parser in `RateService.fetch_and_store` (or extract an `EnvFetcherBase` ABC if you add multiple sources).
2. No other layer needs to change — the repository, alert service, and report service consume `list[Rate]` regardless of origin.

## Adding a new notification channel (e.g. Telegram)

1. Implement a new service (e.g. `telegram_service.py`) with a `send(to, subject, html)` interface matching `EmailService`.
2. Inject it into `AlertService.check_and_notify` and `ReportService.send_due_reports` — no schema or controller changes needed.

## Data flow — scheduled job

```
scheduler._fetch_job()
  └── RateService.fetch_and_store(db)        → hits dolarapi.com, stores list[Rate]
        └── AlertService.check_and_notify(db, rates)
              └── EmailService.send(...)      → fires threshold breach emails
        └── ReportService.send_due_reports(db)
              └── EmailService.send(...)      → fires periodic summary emails
```

## External dependency

Rates are fetched from `https://dolarapi.com/v1/dolares` (no auth required). Each item returns `casa` (type), `nombre` (name), `compra` (buy, nullable), `venta` (sell). Records with `venta: null` are filtered out before storage.
