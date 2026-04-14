# Dollar Tracker

A production-ready FastAPI backend that tracks Argentine dollar exchange rates automatically, stores historical data, fires email alerts when prices cross user-defined thresholds, and sends periodic summary reports — all without manual intervention.

---

## What it does

| Feature | Detail |
|---|---|
| **Automatic rate fetching** | Polls [dolarapi.com](https://dolarapi.com) on a configurable interval (default: every 60 min) and stores every snapshot |
| **Rate history** | Queryable historical data with filters by type, date range, and limit |
| **Statistics** | Min, max, and average sell price over any time window |
| **Price alerts** | Users register an email + a rate type + a min/max threshold. The app emails them the moment the price crosses the boundary, with a configurable cooldown between repeated alerts |
| **Periodic reports** | Users subscribe to hourly, daily, or weekly email summaries with all current rates and 24h stats |
| **Landing page** | Terminal-styled dashboard showing live rates, alert registration form, and report subscription form |
| **Interactive docs** | Auto-generated Swagger UI at `/docs` |

---

## Running locally

```bash
git clone https://github.com/federicomoroz/dollar-tracker.git
cd dollar-tracker

pip install -r requirements.txt

cp .env.example .env
# Fill in SENDGRID_API_KEY and SENDER_EMAIL in .env
# (alerts and reports are silently skipped if these are absent)

uvicorn main:app --reload
```

Open `http://localhost:8000`.

To trigger a rate fetch immediately without waiting for the scheduler:

```bash
curl -X POST http://localhost:8000/rates/fetch
```

---

## Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `SENDGRID_API_KEY` | — | Required for email delivery |
| `SENDER_EMAIL` | — | From-address for all outbound emails |
| `FETCH_INTERVAL_MINUTES` | `60` | How often the scheduler fetches new rates |
| `ALERT_COOLDOWN_HOURS` | `4` | Minimum gap between repeated alerts for the same subscription |

The app starts and serves rates without the email variables. Alerts and reports will log a warning and skip sending rather than crash.

---

## API

| Method | Path | Description |
|---|---|---|
| `GET` | `/rates/current` | Latest rate for each type |
| `GET` | `/rates/history` | Historical rates (`?type=blue&days=7&limit=200`) |
| `GET` | `/rates/stats` | Min/max/avg for a type (`?type=blue&days=1`) |
| `POST` | `/rates/fetch` | Manually trigger a fetch |
| `POST` | `/alerts` | Create a price threshold alert |
| `GET` | `/alerts` | List all alerts |
| `DELETE` | `/alerts/{id}` | Delete an alert |
| `POST` | `/reports` | Subscribe to periodic reports |
| `GET` | `/reports` | List all report subscriptions |
| `DELETE` | `/reports/{id}` | Delete a subscription |

Full schema and try-it-out at `/docs`.

---

## Architecture

### The pattern: MVC + Repository

The app is structured in strict layers. Data flows in one direction only — no layer ever reaches past its immediate neighbor:

```
HTTP Request
     │
     ▼
┌─────────────────────────────────────────────────────────┐
│  Controllers  (app/controllers/)                        │
│                                                         │
│  Parse HTTP input, validate, call one service method,   │
│  return a Pydantic schema. Zero business logic here.    │
└───────────────────────────┬─────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│  Services  (app/models/services/)                       │
│                                                         │
│  All business logic lives here: threshold evaluation,   │
│  cooldown checks, report scheduling, email composition. │
│  Services call repositories — never ORM directly.       │
└───────────────────────────┬─────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│  Repositories  (app/models/repositories/)               │
│                                                         │
│  All database queries. Return ORM objects or dicts.     │
│  No business logic, no HTTP concerns.                   │
└───────────────────────────┬─────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│  ORM Models  (app/models/)                              │
│                                                         │
│  SQLAlchemy table definitions. Pure data — no methods,  │
│  no imports from upper layers.                          │
└─────────────────────────────────────────────────────────┘
```

**Views** (`app/views/`) sit alongside this flow, not inside it:
- `schemas/` — Pydantic models that define what goes in and out of the API. They never touch the database.
- `templates/` — Server-rendered HTML for the landing page. The template calls the existing API via `fetch()` in the browser — it doesn't contain logic.

**Core** (`app/core/`) provides infrastructure to every layer without depending on any of them:
- `config.py` — reads env vars, exposes typed constants
- `database.py` — SQLite engine, session factory, FastAPI `get_db()` dependency
- `scheduler.py` — APScheduler background job that drives the full pipeline on each tick

**Composition root** (`app/main.py`) is the only place that wires everything together: creates the FastAPI instance, registers routers, mounts static files, and manages the scheduler lifecycle.

---

### Why this structure

**Controllers are thin by design.**
A controller's only job is to translate HTTP into a service call and translate the result back into HTTP. When a controller is one or two lines of logic, it's doing its job. This makes routes easy to audit, easy to test, and impossible to accidentally accumulate business rules.

**Services own all decisions.**
Whether an alert should fire, whether a report is due, what the email body looks like — all of that lives in services. This means the scheduler and the HTTP controller can both trigger the same logic without duplicating it, and the logic can be tested in isolation without spinning up a web server.

**Repositories hide the database.**
Services never write a SQL query. They call a repository method with a clear name (`get_active`, `bulk_create`, `update_last_alerted`) and get back domain objects. Swapping SQLite for Postgres, or SQLAlchemy for another ORM, only requires changes in one place.

**The ORM model never escapes its layer.**
Controllers and schemas never import a SQLAlchemy model. Pydantic schemas are constructed from ORM objects via `from_attributes = True` — the boundary is explicit, and serialization concerns don't leak into the database layer.

---

### SOLID in practice

**Single Responsibility** — each class has one reason to change:

| Class | Its one job |
|---|---|
| `RateService` | Fetch from the external API and delegate to the repository |
| `AlertService` | Evaluate thresholds and decide whether to notify |
| `ReportService` | Decide whether a report is due and compose the email |
| `EmailService` | Send an email via SendGrid |
| `RateRepository` | Query the `rates` table |
| `ConsoleReporter` *(envcheck)* | Format and print output |

**Open/Closed** — adding new behavior doesn't require modifying existing classes. A second notification channel (Telegram, Slack) means implementing a new service with the same `send()` interface and injecting it alongside `EmailService`. Nothing else changes.

**Liskov Substitution** — every service can be replaced with a test double. `EmailService.send()` returns `False` when credentials are absent rather than raising — callers don't need to change behavior.

**Interface Segregation** — no class carries methods it doesn't need. `EmailService` has one method. Repositories expose only the queries their service actually uses.

**Dependency Inversion** — high-level modules (scheduler, controllers) depend on service interfaces, not on concrete infrastructure. The database session is injected via FastAPI's `Depends(get_db)`, making the dependency explicit and overridable in tests.

---

### Design patterns

**Repository**
Repositories (`RateRepository`, `AlertRepository`, `ReportRepository`) are the only classes allowed to touch SQLAlchemy directly. Services ask for data by name (`get_active()`, `bulk_create()`, `get_stats()`) and receive domain objects — they're completely decoupled from the query language. Swapping the database engine or ORM requires changes in exactly one place.

**Service Layer**
Services sit between controllers and repositories and own all business decisions. The same `AlertService.check_and_notify()` method is called by both the HTTP controller and the background scheduler — no logic is duplicated, and neither caller cares how the other works.

**Dependency Injection**
The database session is never instantiated inside a service or controller. FastAPI's `Depends(get_db)` injects it from outside, making every endpoint independently testable with a different session (e.g. an in-memory DB). This is constructor injection via the framework rather than by hand.

**Composition Root**
`app/main.py` is the single place in the codebase that knows about concrete types. It creates the FastAPI app, wires all routers, mounts static files, and starts the scheduler. No other module performs wiring — they all receive what they need through FastAPI's dependency system.

**Strategy** (implicit)
`EmailService` is the current notification strategy. Because services only call `EmailService.send(to, subject, html)`, adding a second channel (Telegram, webhook) means writing a new class with that interface and calling it alongside the existing one — no service logic changes. The interface is implicit (duck typing) rather than a formal ABC, which is idiomatic Python.

**Facade**
Each service acts as a facade over its repository. Controllers never need to know whether getting the latest rates involves a subquery, a join, or a cache — they call `RateService.get_latest(db)` and get a list back. The complexity of `get_latest`'s subquery is completely hidden.

**Template / Pipeline**
The scheduler's `_fetch_job()` defines a fixed pipeline: fetch → store → check alerts → send reports. Each step is delegated to a dedicated service. Adding a new step (e.g. push to an external webhook) means adding one line in `_fetch_job()`, not touching any existing service.

---

### Scheduled pipeline

Every `FETCH_INTERVAL_MINUTES` minutes, APScheduler runs:

```
_fetch_job()
  └── RateService.fetch_and_store(db)
        ├── GET https://dolarapi.com/v1/dolares
        ├── Filter out null sell prices
        ├── RateRepository.bulk_create(db, rates)
        └── returns list[Rate]
              │
              ├── AlertService.check_and_notify(db, rates)
              │     ├── AlertRepository.get_active(db)
              │     ├── For each alert: check cooldown, evaluate threshold
              │     ├── EmailService.send(...)
              │     └── AlertRepository.update_last_alerted(db, alert, now)
              │
              └── ReportService.send_due_reports(db)
                    ├── ReportRepository.get_active(db)
                    ├── For each subscription: check frequency delta
                    ├── RateRepository.get_stats(db, ...)  [24h window]
                    ├── EmailService.send(...)
                    └── ReportRepository.update_last_sent(db, report, now)
```

The scheduler never imports controllers or schemas. Controllers never import the scheduler. They both use the same services — that's the only shared surface.

---

## Deployment

The repo includes `render.yaml` for one-click deployment to [Render](https://render.com):

```yaml
services:
  - type: web
    name: dollar-tracker
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
```

Set `SENDGRID_API_KEY` and `SENDER_EMAIL` in Render's Environment dashboard. Everything else has defaults.

---

## Requirements

Python 3.10+. No external database required (SQLite, file-based).

```
fastapi, uvicorn, sqlalchemy, httpx, sendgrid, apscheduler, pydantic[email], aiofiles
```
