# API Sentinel

**Catch API validation issues before your users do.**

An AI-powered quality analyzer that automatically stress-tests HTTP endpoints, scores their validation robustness 0–100, and delivers bilingual actionable insights — all through a modern SaaS dashboard with scheduling and persistent history.

---

## Overview

Most API bugs in production aren't logic errors — they're validation failures. An endpoint that accepts a missing payload, swallows integers where strings are expected, or ignores incomplete data is a ticking clock.

API Sentinel runs a parallel battery of edge-case tests against any endpoint, analyzes how it handles bad input, and produces a quality score with severity classification and LLM-generated insights in Spanish and English.

Built for developers who want fast, automated signal about API health without writing custom test suites from scratch.

---

## Key Features

- **AI insights** — local LLM (`qwen3:8b` via Ollama) analyzes results and generates bilingual, actionable insights; falls back to rule-based dispatch if Ollama is unavailable
- **Parallel test execution** — all test cases run concurrently via `ThreadPoolExecutor` (4 workers)
- **Smart test generation** — GET without payload → 1–2 tests; POST/PUT/PATCH → up to 4 cases (valid, missing payload, invalid types, incomplete payload); DELETE → 1 test
- **Custom test cases** — define your own cases with name, payload, headers, and `expected_status`; they run in parallel with auto-generated cases
- **Scheduled tests** — cron-based scheduling (APScheduler) with presets (every 5 min, hourly, daily); toggle on/off without deleting
- **Saved configurations** — persist URL + method + payload + headers + base URL combos; load any config with one click
- **Base URL** — set a global base URL and use relative paths (e.g. `/users`) in all configs; persisted per config
- **0–100 quality score** — multi-factor scoring with differentiated 4xx/5xx penalties, latency deductions, and functional gap detection
- **Severity classification** — CRITICAL / HIGH / MEDIUM / LOW based on signals (not score thresholds)
- **Response body analysis** — captures the first 500 chars of each response; detects false positives (HTTP 200 with error content in body)
- **Test history** — SQLite-backed, paginated (20 per page), filterable by URL and severity; click any row to reload the full result
- **JSON export** — download any result as a structured report
- **Dark mode SaaS dashboard** — bilingual (ES/EN), KPI cards, severity badges, toast notifications

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+, FastAPI, Uvicorn |
| AI Engine | Ollama (`qwen3:8b`) — local LLM via REST |
| HTTP Testing | `requests`, `ThreadPoolExecutor` (parallel) |
| Analysis Engine | Rule-based issue detection + signal-based severity |
| Scheduling | APScheduler 3.x (BackgroundScheduler, CronTrigger) |
| Persistence | SQLite via `sqlite3` — Repository pattern |
| Validation | Pydantic v2 |
| Frontend | HTML5, Vanilla JS, CSS3 (dark mode) |

---

## Requirements

- Python 3.11+
- [Ollama](https://ollama.com) running locally with `qwen3:8b` pulled *(optional — rule-based fallback always available)*

```bash
ollama pull qwen3:8b
```

---

## Installation

```bash
git clone git@github.com:ivanpr87/Probador_APIs.git
cd Probador_APIs

python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows

pip install fastapi uvicorn requests apscheduler pydantic

uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000` in your browser.

---

## Project Structure

```
.
├── app/
│   ├── main.py                          # FastAPI app, lifespan, routers, no-cache middleware
│   ├── api/routes/
│   │   ├── test_routes.py               # POST /run-test, GET /history, GET /history/{id}
│   │   ├── configs_routes.py            # GET/POST/DELETE /configs
│   │   └── scheduler_routes.py          # GET/POST/DELETE/PATCH /schedules
│   ├── services/
│   │   ├── test_service.py              # Test generation + parallel execution
│   │   ├── analysis_service.py          # Scoring engine, issue detection, severity, insights
│   │   ├── ai_service.py                # Ollama integration + bilingual fallback
│   │   ├── report_service.py            # JSON export builder
│   │   └── scheduler_service.py         # APScheduler lifecycle + job registration
│   ├── repositories/
│   │   ├── test_repository.py           # SQLite: test history CRUD
│   │   ├── configs_repository.py        # SQLite: saved configs CRUD
│   │   └── scheduler_repository.py      # SQLite: schedules CRUD + toggle + last_run
│   ├── models/
│   │   ├── request_models.py            # Pydantic input schemas (TestRequest, CustomTestCase)
│   │   ├── response_models.py           # Pydantic output schemas
│   │   └── scheduler_models.py          # Schedule schemas (ScheduleCreate, Schedule)
│   ├── core/
│   │   ├── config.py                    # App settings (Ollama URL, model, timeouts, DB path)
│   │   └── database.py                  # SQLite init, WAL mode, schema creation
│   ├── utils/
│   │   └── http_client.py               # HTTP executor (5s timeout, body capture)
│   └── static/
│       ├── index.html                   # SaaS dashboard shell (4 views)
│       ├── app.js                       # Frontend logic, i18n, rendering, state
│       └── styles.css                   # Design system (dark mode, KPI cards, badges)
├── sentinel.db                          # SQLite database (auto-created)
├── .gitignore
└── README.md
```

---

## How It Works

```
1. User submits URL + method + optional payload + optional custom test cases
        ↓
2. Test generator creates edge-case variants:
   DELETE → 1 test (valid_request)
   GET without payload → 1-2 tests
   POST/PUT/PATCH → up to 4 tests:
     · valid_request       — original payload
     · missing_payload     — None (test if server rejects)
     · invalid_types       — int↔string swaps per field
     · incomplete_payload  — first key removed
   Custom cases appended and executed in parallel
        ↓
3. ThreadPoolExecutor (4 workers) runs all tests in parallel
   Each result captures: status code, response time, body (500 chars), error
        ↓
4. Analysis engine detects issues (5 categories):
   · HTTP codes       — 4xx/5xx with bilingual catalogue
   · Functional       — missing payload accepted, invalid types accepted, false positives
   · Latency          — avg >700 ms (MEDIUM), avg >1200 ms (HIGH)
   · Schema           — field presence and type validation vs expected_schema
   · Network          — connection errors, unreachable endpoints
        ↓
5. Scoring (0–100) with differentiated 4xx/5xx model:
   5xx → ceiling 40 | only 4xx → floor 40
        ↓
6. Severity derived from signals (not score):
   5xx/unreachable → CRITICAL | 100% fail → HIGH | 4xx → MEDIUM | clean → LOW
        ↓
7. Ollama qwen3:8b generates bilingual insights
   (falls back to type-dispatch rule engine if Ollama unavailable)
        ↓
8. Result saved to SQLite + returned to dashboard
```

---

## API Endpoints

### `POST /run-test`

**Request**

```json
{
  "url": "https://api.example.com/users",
  "method": "POST",
  "payload": { "name": "Ivan", "age": 30 },
  "headers": { "Authorization": "Bearer <token>" },
  "base_url": "https://api.example.com",
  "expected_schema": { "id": "int", "name": "string" },
  "custom_test_cases": [
    {
      "name": "test_admin_user",
      "payload": { "name": "Admin", "role": "admin" },
      "headers": { "X-Role": "admin" },
      "expected_status": 201
    }
  ]
}
```

**Response**

```json
{
  "total_tests": 5,
  "results": [
    {
      "test_name": "valid_request",
      "status_code": 201,
      "response_time": 0.142,
      "response_body": "{\"id\": 101, \"name\": \"Ivan\"}",
      "error": null
    }
  ],
  "issues_detected": ["..."],
  "severity": "MEDIUM",
  "quality_score": 75,
  "ai_insights": ["..."],
  "summary": {
    "total": 5,
    "passed": 4,
    "failed": 1,
    "fail_rate": 20.0
  }
}
```

### `GET /history` · `GET /history/{id}`

```
GET /history?url_filter=api.example&severity_filter=CRITICAL&page=1
```

### `GET /configs` · `POST /configs` · `DELETE /configs/{id}`

```json
{
  "name": "My Auth Endpoint",
  "url": "/auth",
  "method": "POST",
  "payload": { "username": "test", "password": "secret" },
  "headers": { "X-API-Key": "abc123" },
  "base_url": "https://api.example.com"
}
```

Returns `201` on create · `409` if name already exists.

### `GET /schedules` · `POST /schedules` · `DELETE /schedules/{id}` · `PATCH /schedules/{id}/toggle`

```json
{
  "name": "Hourly health check",
  "config_id": 3,
  "cron": "0 * * * *"
}
```

---

## Scoring Model

### Quality Score (0–100)

Starting from 100, penalties are applied in priority order:

| Signal | Penalty |
|---|---|
| 5xx or unreachable endpoint | Ceiling: max score = 40 |
| Only 4xx (no 5xx) | Floor: min score = 40 |
| Each failed test | −10 pts |
| 100% failure rate + 5xx | −50 pts |
| 100% failure rate, only 4xx | −30 pts |
| Failure rate > 50% | −20 pts |
| Each 4xx response | −5 pts (capped at −30) |
| Average latency > 1200 ms | −10 pts |
| Average latency > 700 ms | −5 pts |
| Invalid types accepted | −20 pts |
| Missing payload accepted | −10 pts |
| False positive (200 + error body) | −5 pts |

### Score Interpretation

| Score | Rating | Meaning |
|---|---|---|
| 85–100 | Excellent | Strong validation — no significant gaps |
| 65–84 | Good | Minor issues, low production risk |
| 40–64 | Fair | Validation gaps — review before deploy |
| 0–39 | Critical | Multiple failures — significant production risk |

### Severity Levels

Severity is derived from signals, not score thresholds:

| Level | Triggered by |
|---|---|
| CRITICAL | 5xx response or endpoint unreachable |
| HIGH | 100% test failure rate (without 5xx) |
| MEDIUM | Any 4xx response, or any unclassified failure |
| LOW | Zero failures — clean run |

---

## Limitations

- **Auth headers are pass-through** — no OAuth flows or token refresh; paste a bearer token manually
- **Static test generation** — edge cases are type-based; domain-specific business logic is not inferred
- **Latency scoring is average-based** — no p95/p99 percentiles
- **SQLite** — suitable for local use; migrate to PostgreSQL for production (only `database.py` needs to change — Repository pattern is in place)
- **Ollama must be running locally** — no cloud LLM fallback; rule-based insights are used if Ollama is unreachable
- **No unit tests** — engine correctness validated manually

---

## Future Improvements

- [ ] OAuth 2.0 / token-refresh support for protected endpoints
- [ ] OpenAPI / Swagger spec import for automated endpoint discovery
- [ ] PDF export with branded report layout
- [ ] Load testing mode (concurrent users, percentile latency, error rate under load)
- [ ] Full-text search in history
- [ ] Webhook / Slack notifications on scheduled test failure
- [ ] Response time percentiles (p50, p95, p99) per test run
- [ ] Per-schedule API key / auth token override
- [ ] Docker + docker-compose for one-command deployment
- [ ] `.env` support for runtime configuration (Ollama URL, timeouts)
- [x] All HTTP methods (GET, POST, PUT, PATCH, DELETE)
- [x] Saved test configurations
- [x] Scheduled tests with cron expressions
- [x] Custom test cases defined by the user
- [x] Base URL configurable and persisted per config
- [x] Test history with pagination and filters
- [x] Bilingual AI insights (ES/EN)

---

## Author

**Ivan Bastos** — AI Automation Specialist & Product-Oriented Builder  
Buenos Aires, Argentina

Focused on building Hybrid analysis engine (rule-based + LLM insights) tools that solve real engineering problems.

[ivanbastos18@gmail.com](mailto:ivanbastos18@gmail.com) · [GitHub](https://github.com/ivanpr87)

---

## License

MIT
