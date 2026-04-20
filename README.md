# API Sentinel

**Catch API validation issues before your users do.**

An AI-powered quality analyzer that automatically stress-tests HTTP endpoints using a local LLM, scores their validation robustness, and delivers bilingual actionable insights — all through a modern SaaS dashboard.

---

## Overview

Most API bugs in production aren't logic errors — they're validation failures. An endpoint that accepts a missing payload, swallows integers where strings are expected, or ignores incomplete data is a ticking clock.

API Sentinel runs a parallel battery of edge-case tests against any endpoint, analyzes how it handles bad input — including response body content — and produces a 0–100 quality score with severity classification and LLM-generated insights in Spanish and English.

Built for developers who want fast, automated signal about API health without writing custom test suites from scratch.

---

## Key Features

- **Real AI insights** — local LLM (`qwen3:8b` via Ollama) analyzes test results and generates bilingual, actionable insights specific to each endpoint; falls back to rule-based insights if Ollama is unavailable
- **Parallel test execution** — all test cases run concurrently via `ThreadPoolExecutor`, reducing total test time by up to 4×
- **Smart test generation** — GET endpoints without payload run only meaningful tests; POST endpoints run the full validation suite (valid, missing, invalid types, incomplete)
- **Response body analysis** — captures the first 500 chars of each response and detects false positives (HTTP 200 with error content in body)
- **Response time scoring** — slow responses (>1.5s warn, >3s critical) reduce the quality score and trigger dedicated insights
- **0–100 quality score** — multi-factor scoring: validation gaps, false positives, and response time penalties
- **Severity classification** — Low / High / Critical rating surfaced instantly
- **Live dashboard** — dark-mode SaaS UI with KPI cards, score bars, severity badges, body preview column, and toast notifications
- **Bearer token shortcut** — dedicated auth token field auto-injects `Authorization: Bearer <token>` header across all test cases
- **Test history with pagination** — SQLite-backed persistence with page navigation (20 per page); click any row to reload the full result
- **Saved configurations** — name and persist URL + method + payload + headers combos; load any saved config into the form with one click
- **JSON export** — download any result as a structured report

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+, FastAPI, Uvicorn |
| AI Engine | Ollama (`qwen3:8b`) via REST API |
| HTTP Testing | `requests` library, `ThreadPoolExecutor` (parallel) |
| Analysis Engine | Rule-based issue detection + LLM insight generation |
| Persistence | SQLite via `sqlite3` (Repository pattern) |
| Frontend | HTML5, Vanilla JavaScript, CSS3 (dark mode design system) |

---

## Requirements

- Python 3.11+
- [Ollama](https://ollama.com) running locally with `qwen3:8b` pulled

```bash
# Pull the model (one-time setup)
ollama pull qwen3:8b
```

> **Note:** Ollama is optional. If unavailable, the system falls back to bilingual rule-based insights automatically — no configuration needed.

---

## Installation

```bash
# Clone the repository
git clone git@github.com:ivanpr87/Probador_APIs.git
cd Probador_APIs

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows

# Install dependencies
pip install fastapi uvicorn requests

# Start the server
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000` in your browser.

---

## Project Structure

```
.
├── app/
│   ├── main.py                      # FastAPI app + no-cache middleware + static serving
│   ├── api/routes/
│   │   ├── test_routes.py           # POST /run-test, GET /history, GET /history/{id}
│   │   └── configs_routes.py        # GET/POST/DELETE /configs
│   ├── services/
│   │   ├── test_service.py          # Test generation + parallel execution + orchestration
│   │   ├── analysis_service.py      # Issue detection, response time scoring, severity
│   │   ├── ai_service.py            # Ollama integration + bilingual fallback insights
│   │   └── report_service.py        # JSON export builder
│   ├── repositories/
│   │   ├── test_repository.py       # SQLite persistence (history CRUD)
│   │   └── configs_repository.py    # SQLite persistence (saved configs CRUD)
│   ├── models/
│   │   ├── request_models.py        # Pydantic input schemas
│   │   └── response_models.py       # Pydantic output schemas
│   ├── core/
│   │   ├── config.py                # App settings (Ollama URL, model, timeouts)
│   │   └── database.py              # SQLite connection + schema init
│   ├── utils/
│   │   └── http_client.py           # HTTP executor (5s timeout, body capture)
│   └── static/
│       ├── index.html               # SaaS dashboard shell
│       ├── app.js                   # Frontend logic (navigation, rendering, toasts)
│       └── styles.css               # Design system (dark mode, KPI cards, history table)
├── .gitignore
└── README.md
```

---

## How It Works

```
1. User submits URL + method + optional payload
        ↓
2. Test generator creates 1–4 edge-case variants
   (GET without payload → 1-2 tests; POST → up to 4)
        ↓
3. ThreadPoolExecutor runs all tests in parallel
   Each result captures: status code, response time, body (500 chars)
        ↓
4. Analysis engine detects issues:
   · Missing payload accepted (−30 pts)
   · Invalid types accepted (−40 pts)
   · False positive: 200 with error in body (−15 pts)
   · Slow response time: >1.5s (−10 pts), >3s (−20 pts)
        ↓
5. Ollama qwen3:8b generates bilingual insights
   (falls back to rule-based if Ollama unavailable)
        ↓
6. Result saved to SQLite + returned to dashboard
```

---

## API Usage

### `POST /run-test`

**Request**

```json
{
  "url": "https://api.example.com/users",
  "method": "POST",
  "payload": { "name": "Ivan", "age": 30 },
  "headers": { "Authorization": "Bearer your-token" }
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `url` | string | Yes | Target endpoint URL |
| `method` | string | Yes | `GET` or `POST` |
| `payload` | object | No | Base JSON body for POST requests |
| `headers` | object | No | Auth or custom headers passed to all test cases |

**Response**

```json
{
  "total_tests": 4,
  "results": [
    {
      "test_name": "valid_request",
      "status_code": 201,
      "response_time": 0.142,
      "response_body": "{\"id\": 101, \"name\": \"Ivan\"}",
      "error": null
    }
  ],
  "issues_detected": [
    "La API acepta solicitudes sin payload — falta validación · API accepts requests without payload — required field validation is missing"
  ],
  "severity": "high",
  "quality_score": 70,
  "ai_insights": [
    "[ES] Implementar validación de campos requeridos en el middleware · [EN] Add required field validation at the middleware layer"
  ]
}
```

### `GET /configs` · `POST /configs` · `DELETE /configs/{id}`

Manage saved test configurations.

**POST /configs request**

```json
{
  "name": "My Auth Endpoint",
  "url": "https://api.example.com/auth",
  "method": "POST",
  "payload": { "username": "test" },
  "headers": { "X-API-Key": "abc123" }
}
```

Returns `201` with the saved config object (including `id` and `created_at`). Returns `409` if the name already exists.

---

## Interpreting Results

### Quality Score

| Score | Rating | Meaning |
|---|---|---|
| 80–100 | Excellent | Strong validation — no significant gaps detected |
| 70–79 | Good | Minor issues, low production risk |
| 40–69 | Fair | Validation gaps detected — review before deploy |
| 0–39 | Critical | Multiple failures — significant production risk |

**Scoring penalties:**

| Issue | Penalty |
|---|---|
| API accepts missing payload | −30 pts |
| API accepts invalid data types | −40 pts |
| False positive (200 + error in body) | −15 pts |
| Response time >1.5s average | −10 pts |
| Response time >3.0s average | −20 pts |

### Severity Levels

| Level | Color | Triggered by |
|---|---|---|
| Low | Green | No issues detected |
| High | Orange | Missing payload accepted, or slow response time |
| Critical | Red | Invalid data types accepted without error |

---

## Use Cases

- **Backend developers** — quick sanity check before shipping an endpoint
- **QA engineers** — automated first-pass validation testing without writing fixtures
- **Code reviewers** — verify that a new endpoint enforces its own contracts
- **API consumers** — assess the reliability of a third-party API you depend on

---

## Why This Matters

APIs that don't validate their inputs fail silently. A missing required field might cause a null reference downstream. An integer where a string is expected might corrupt a database record. A 200 response with an error in the body is a contract violation that slips past every status-code-only monitor.

API Sentinel makes that early detection automatic — no test suite to maintain, no fixtures to write. Paste a URL, run the test, and get LLM-generated insights in seconds.

---

## Limitations

- **GET and POST only** — PUT, PATCH, DELETE are not supported in this version
- **Static test generation** — edge cases are type-based; domain-specific business logic is not inferred
- **Auth headers are pass-through only** — no OAuth flows or token refresh; paste a bearer token manually if needed
- **SQLite** — suitable for local use and demos; migrate to PostgreSQL for production (only `database.py` needs to change, Repository pattern is already in place)
- **Ollama must be running locally** — no cloud LLM fallback; rule-based insights are used if Ollama is unreachable

---

## Future Improvements

- [ ] Additional HTTP methods (PUT, PATCH, DELETE)
- [ ] OAuth 2.0 / token-refresh support for protected endpoints
- [ ] History search and filtering
- [x] Saved test configurations (name and reuse URL + payload combos)
- [ ] PDF export with branded report layout
- [ ] Custom test case editor for domain-specific edge cases
- [ ] OpenAPI spec import for automated endpoint discovery
- [ ] Load testing mode (concurrent requests, percentile latency)

---

## Author

**Ivan Bastos** — AI Automation Specialist & Product-Oriented Builder  
Buenos Aires, Argentina

Focused on building AI-powered tools that solve real engineering problems. Open to collaboration and feedback.

[ivanbastos18@gmail.com](mailto:ivanbastos18@gmail.com) · [GitHub](https://github.com/ivanpr87)

---

## License

MIT
