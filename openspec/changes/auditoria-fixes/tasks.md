# Tasks: Auditoría Fixes — 15 Issues from Deep Code Audit

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~440 |
| 400-line budget risk | Medium |
| Chained PRs recommended | Yes |
| Suggested split | 3 PRs |
| Delivery strategy | auto-chain |
| Chain strategy | feature-branch-chain |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: feature-branch-chain
400-line budget risk: Medium

### Chained PR Plan

| PR | Branch | Base | Scope | Lines |
|----|--------|------|-------|-------|
| 1 | `fix/auditoria-fixes-critical` | `fix/auditoria-fixes` | AF-001,002,014 + tests | ~112 |
| 2 | `fix/auditoria-fixes-security` | PR #1 | AF-003,004,005,006 + tests | ~120 |
| 3 | `fix/auditoria-fixes-perf-struct` | PR #2 | AF-007,008,010(rest),011,012,013,015 | ~208 |

Tracker `fix/auditoria-fixes` accumulates all 3 PRs, then merges to main.

## Phase 1: Critical (PR #1)

- [x] 1.1 `app/utils/http_client.py:19-24` → `requests.request(method, url, json=payload, headers=req_headers, timeout=...)` — remove if/elif/else [AF-001]
- [x] 1.2 `app/services/analysis_service.py:518` → `"total"`→`"total_tests"` in `_build_summary`; update `analyze()` docstring [AF-002]
- [x] 1.3 `app/services/test_service.py:122-124` → Remove workaround mapping `"total"`→`"total_tests"` (after 1.2) [AF-002]
- [x] 1.4 `app/services/test_service.py:67` → `.pop("_headers")`→`.get("_headers")` [AF-014]
- [x] 1.5 `tests/services/test_analysis_service.py:23-29` → `_make_summary` helper key, line 256 assertion: `"total"`→`"total_tests"` [AF-002]

## Phase 2: Security (PR #2)

- [ ] 2.1 `app/models/request_models.py` → `@field_validator("url")` SSRF blocklist via `ipaddress`+`socket.getaddrinfo(timeout=2)`. Block: 127/8, 10/8, 172.16/12, 192.168/16, 169.254/16, ::1, fc00::/7 [AF-003]
- [ ] 2.2 `app/api/routes/configs_routes.py:25,39` → Replace `detail=str(e)` with `"Internal server error"`; add `logger.error(exc_info=True)` [AF-004]
- [ ] 2.3 `app/core/config.py` → Add `ENCRYPTION_KEY: str` setting (env var, no default) [AF-005]
- [ ] 2.4 `app/repositories/configs_repository.py` → Fernet encrypt on save (line 22), decrypt on read via `_row_to_config`; log warning if key missing — fallback plaintext [AF-005]
- [ ] 2.5 `requirements.txt` → Add `cryptography==44.0.0` [AF-005]
- [ ] 2.6 `app/core/database.py:53,56` → `except Exception`→`except sqlite3.OperationalError`; real errors (disk I/O, corruption) must propagate [AF-006]

## Phase 3: Performance (PR #3)

- [x] 3.1 `app/repositories/test_repository.py` → Add `fetch_previous_scores_batch(rows, source)` via `GROUP BY url, method` with `MAX(json_extract(result,'$.quality_score')) WHERE id < ?` [AF-007]
- [x] 3.2 `app/services/history_service.py:27-32` → Replace per-row `fetch_previous_comparable_result()` with single batch call from 3.1 [AF-007]
- [x] 3.3 `app/repositories/configs_repository.py` → Add `config_exists(config_id: int) -> bool` via `SELECT 1 FROM saved_configs WHERE id = ?` [AF-008]
- [x] 3.4 `app/api/routes/scheduler_routes.py:36-37` → `list_configs()+any()`→`config_exists(data.config_id)` [AF-008]
- [x] 3.5 `app/services/scheduler_service.py:75-76` → `list_configs()+next()`→`get_config_by_id()` or `config_exists()+fetch` [AF-008]

## Phase 4: Tests (split across PRs)

- [x] 4.1 CREATE `tests/utils/test_http_client.py` — ≥5 tests: GET/POST/PUT/PATCH/DELETE + timeout + ConnectionError. Mock `requests.request` [AF-009] ▶ PR #1 (11 tests)
- [x] 4.2 ADD `tests/services/test_test_service.py` — `_execute_case` mutation fix test + `_build_summary` key test [AF-010] ▶ PR #1 (3 tests: mutation fix + headers behavior)
- [ ] 4.3 ADD SSRF tests — private IPs rejected with 422, public URLs pass. Inline or `tests/models/test_request_models.py` [AF-003] ▶ PR #2
- [ ] 4.4 ADD encryption roundtrip tests — save encrypted, read decrypted, missing key warning. In `tests/repositories/test_configs_repository.py` [AF-005] ▶ PR #2
- [x] 4.5 CREATE `tests/services/test_test_service.py` (remaining) — Case generation for GET/POST/PUT/PATCH/DELETE + custom cases + `run_test` flow (mock `send_request`, `analyze`, `save_result`) [AF-010] ▶ PR #3
- [x] 4.6 CREATE `tests/services/test_scheduler_service.py` — ≥6 tests: register/remove/toggle jobs + `_run_scheduled_test` success + error paths. Mock `BackgroundScheduler` + repo functions [AF-011] ▶ PR #3

## Phase 5: Structural (PR #3)

- [x] 5.1 `app/services/auth_service.py:9` → Add `import threading; _TOKEN_LOCK = threading.Lock()`; guard `_TOKEN_CACHE` writes with context manager [AF-012]
- [x] 5.2 `app/services/scheduler_service.py:62-70` → Move lazy imports to module level; verify `python -c "import app.main"` succeeds [AF-013]
- [x] 5.3 `app/core/database.py:11` → Add comment: `# check_same_thread=False — intentional for WAL-mode multi-thread access. get_connection() ensures one connection per query.` [AF-015]

## Verification

- [x] `pytest tests/ -v` — all existing + 19+ new tests pass (155/155!)
- [ ] `python -c "import app.main"` — no circular imports
- [ ] PUT/PATCH/DELETE endpoints return valid results (not "Unsupported")
- [ ] Private IPs rejected with 422; public URLs pass
- [ ] 500 errors return `"Internal server error"` — no `str(e)` in response
- [ ] `auth_config` column contains ciphertext, not plaintext, in `saved_configs`
