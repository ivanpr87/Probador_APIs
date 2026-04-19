# API Sentinel

**Catch API validation issues before your users do.**

An AI-powered quality analyzer that automatically stress-tests HTTP endpoints, scores their validation robustness, and delivers actionable insights — all through a modern SaaS dashboard.

---

## Overview

Most API bugs in production aren't logic errors — they're validation failures. An endpoint that accepts a missing payload, swallowed integers where strings are expected, or ignores incomplete data is a ticking clock.

API Sentinel runs a structured battery of edge-case tests against any endpoint, analyzes how it handles bad input, and produces a 0–100 quality score with severity classification and plain-English recommendations.

Built for developers who want fast, automated signal about API health without writing custom test suites from scratch.

---

## Key Features

- **Automated edge-case generation** — sends four test variants per request: valid payload, missing payload, invalid data types, and incomplete payload
- **Validation gap detection** — identifies whether the API enforces required fields and correct data types
- **0–100 quality score** — deterministic, penalty-based scoring tied to specific failure categories
- **Severity classification** — Low / High / Critical rating surfaced instantly
- **AI-style insights** — plain-English descriptions of what failed and why it matters in production
- **Live dashboard** — dark-mode SaaS UI with score bars, severity badges, and a per-test results table
- **Zero config** — no auth setup, no YAML files; paste a URL and run

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.8+, FastAPI |
| HTTP Testing | `requests` library (5s timeout) |
| Analysis Engine | Custom rule-based + scoring system |
| Frontend | HTML5, Vanilla JavaScript, CSS3 |
| Serving | Uvicorn (ASGI) |

---

## Installation

**Requirements:** Python 3.8+

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
│   ├── main.py                 # FastAPI app + static file serving
│   ├── routes/
│   │   └── test_routes.py      # POST /run-test endpoint
│   └── services/
│       ├── test_generator.py   # Generates 4 test case variants
│       ├── test_service.py     # Orchestrates execution + aggregation
│       ├── analyzer.py         # Detects validation issues from results
│       └── ai_analyzer.py      # Scoring logic + insight generation
│   └── static/
│       └── index.html          # SaaS dashboard (self-contained)
├── .gitignore
└── README.md
```

---

## API Usage

### `POST /run-test`

Runs the full test suite against a target endpoint.

**Request**

```json
{
  "url": "https://api.example.com/users",
  "method": "POST",
  "payload": {
    "name": "Ivan",
    "age": 30
  }
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `url` | string | Yes | Target endpoint URL |
| `method` | string | Yes | `GET` or `POST` |
| `payload` | object | No | Base JSON body for POST requests |

**Response**

```json
{
  "total_tests": 4,
  "results": [
    {
      "test_name": "valid_request",
      "status_code": 200,
      "response_time": 0.142,
      "error": null
    },
    {
      "test_name": "missing_payload",
      "status_code": 200,
      "response_time": 0.138,
      "error": null
    }
  ],
  "issues_detected": [
    "API accepts requests without payload — missing field validation"
  ],
  "severity": "high",
  "quality_score": 70,
  "ai_insights": [
    "The API does not validate required fields. It may accept incomplete requests silently."
  ]
}
```

---

## How to Use the Dashboard

1. Enter the endpoint URL you want to test
2. Select the HTTP method (GET or POST)
3. Paste a JSON payload if testing a POST endpoint
4. Click **Run AI Test**
5. Review your results:
   - Quality score with color-coded progress bar
   - Severity badge (Low / High / Critical)
   - Test-by-test breakdown table
   - Detected issues list
   - AI insights with production risk context

---

## Interpreting Results

### Quality Score

| Score | Rating | Meaning |
|---|---|---|
| 80–100 | Excellent | Strong validation — API enforces required fields and types |
| 70–79 | Good | Minor gaps, low production risk |
| 40–69 | Fair | Validation issues detected — review before deploy |
| 0–39 | Critical | Multiple failures — significant production risk |

**Scoring penalties:**
- −30 points: API accepts requests with missing payload
- −40 points: API accepts requests with invalid data types

### Severity Levels

| Level | Color | Triggered by |
|---|---|---|
| Low | Green | No issues detected |
| High | Orange | Missing payload accepted without error |
| Critical | Red | Invalid data types accepted without error |

---

## Use Cases

- **Backend developers** — quick sanity check before shipping an endpoint
- **QA engineers** — automated first-pass validation testing without writing fixtures
- **Code reviewers** — verify that a new endpoint enforces its own contracts
- **API consumers** — assess the reliability of a third-party API you depend on

---

## Why This Matters

APIs that don't validate their inputs fail silently. A missing required field might cause a null reference downstream. An integer where a string is expected might corrupt a database record. These issues are cheap to detect early and expensive to debug in production.

API Sentinel makes that early detection automatic — no test suite to maintain, no fixtures to write. Paste a URL, run the test, and know immediately whether your API is enforcing its contracts.

---

## Limitations

- **No authentication support** — tests are sent without auth headers; private APIs will return 401/403
- **POST and GET only** — PUT, PATCH, DELETE are not supported in this version
- **No load testing** — tests run sequentially with a single request per case
- **Static test generation** — edge cases are type-based (missing, wrong types, incomplete); domain-specific logic is not inferred
- **No history or persistence** — results are not stored between sessions

---

## Future Improvements

- [ ] Auth header support (Bearer token, API key)
- [ ] Additional HTTP methods (PUT, PATCH, DELETE)
- [ ] Export results as JSON or PDF report
- [ ] Test history with session persistence
- [ ] Custom test case editor
- [ ] OpenAPI spec import for automated endpoint discovery

---

## Author

**Ivan Bastos** — AI Automation Specialist & Product-Oriented Builder  
Buenos Aires, Argentina

Focused on building AI-powered tools that solve real engineering problems. Open to collaboration and feedback.

[ivanbastos18@gmail.com](mailto:ivanbastos18@gmail.com) · [GitHub](https://github.com/ivanpr87)

---

## License

MIT
