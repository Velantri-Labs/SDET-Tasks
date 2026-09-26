# Bugs

All of these were reproduced against a running instance, not inferred from reading the code alone.

## Summary crashes with 500 when passed + failed is 0

- Severity: P1
- Endpoint: `GET /api/runs/{id}/summary`
- Steps:
  1. `POST /api/runs` with `{"name": "login", "tests": ["opens"]}`
  2. `GET /api/runs/1/summary` (no results submitted yet)
- Expected: `200` with `pass_rate: 0.0`
- Actual: `500 {"error": "internal error"}` (unhandled `ZeroDivisionError`, caught only by a generic handler)
- Contract rule it breaks: "When `passed + failed` is `0`, `pass_rate` is `0.0`. This endpoint does not return an error for that case." This fires on the most common possible call — summarizing a run right after creation, before any results exist. The same crash happens if every submitted result is `skip`.

## Unknown run id on summary returns 200 with fake data instead of 404

- Severity: P1
- Endpoint: `GET /api/runs/{id}/summary`
- Steps: `GET /api/runs/999/summary` where run 999 was never created
- Expected: `404 {"error": "..."}`
- Actual: `200 {"id": 999, "name": null, "status": "queued", "total": 0, ...}`
- Contract rule it breaks: "Unknown run id → `404` and `{ "error": "..." }`." The store's `summary()` never raises for a missing run; it returns a placeholder dict, and the route has no check at all.

## Duplicate result for the same test overwrites instead of being rejected

- Severity: P1
- Endpoint: `POST /api/runs/{id}/results`
- Steps:
  1. Create a run with test `"opens"`.
  2. `POST` a result `{"test": "opens", "status": "pass", "duration_ms": 12}` → 200.
  3. `POST` again `{"test": "opens", "status": "fail", "duration_ms": 5}`.
- Expected: second call is `400`, and the run's stored result for `opens` stays `pass` / `12`.
- Actual: second call returns `200`, and the stored result is silently replaced with `fail` / `5` (confirmed via the summary, which then reports `failed` where it should still report `passed`).
- Contract rule it breaks: "Each test accepts one result. A second result for the same test → `400`, and the first result stays as it was." There is no existence check before the store write.

## Status is checked case-insensitively but stored and returned unnormalized

- Severity: P1
- Endpoint: `POST /api/runs/{id}/results`
- Steps: Submit `{"test": "opens", "status": "PASS", "duration_ms": 7}`
- Expected: `200 {"...", "status": "pass", ...}`, and the run's summary counts this test toward `passed`.
- Actual: `200 {"...", "status": "PASS", ...}` — response is not normalized, and the summary's `passed` counter (which compares `item["status"] == "pass"`) does not count it, because the raw, un-lowered string is what got stored.
- Contract rule it breaks: "Normalize `status` by trimming and lowercasing... Store the normalized value" and "`status` in this body is the normalized value." Validation is case-insensitive but storage is not, so counts silently drift from what was actually validated.

## Summary status reports "passed" before all tests have results

- Severity: P1
- Endpoint: `GET /api/runs/{id}/summary`
- Steps:
  1. Create a run with two tests, `opens` and `submits`.
  2. Submit a `pass` result only for `opens`.
  3. `GET` the summary.
- Expected: `status: "running"` (this is the exact worked example in the contract: `total: 2, passed: 1` → `"running"`).
- Actual: `status: "passed"`.
- Contract rule it breaks: "`passed` when every test has a result and none of them is `fail`" / "`running` when at least one result is in, none is `fail`, and at least one test has no result yet." The code takes the `elif passed:` branch (any pass count > 0) before ever checking whether every test has reported, so it produces "passed" the moment any single test passes, regardless of how many tests are still outstanding.

## pass_rate wrongly includes skips in its denominator

- Severity: P2
- Endpoint: `GET /api/runs/{id}/summary`
- Steps:
  1. Create a run with tests `a` and `b`.
  2. Submit `a` as `pass`, `b` as `skip`.
  3. `GET` the summary.
- Expected: `pass_rate: 1.0` (`passed / (passed + failed)` = `1 / 1`)
- Actual: `pass_rate: 0.5` (code uses `passed / len(results)` = `1 / 2`, pulling the skip into the denominator)
- Contract rule it breaks: "`pass_rate` is `passed / (passed + failed)`. Skips are not part of that ratio."

## Run name is never trimmed and has no length ceiling

- Severity: P2
- Endpoint: `POST /api/runs`
- Steps:
  - `POST` with `name: "  login  "` → stored and returned as `"  login  "`, not `"login"`.
  - `POST` with `name: "x" * 41` (41 chars) → accepted (`201`) instead of rejected.
  - `POST` with `name: "    "` (whitespace only) → accepted (`201`) instead of rejected as empty-after-trim.
- Expected: name is trimmed before storing/returning; length is enforced at 1-40 chars post-trim.
- Actual: raw string stored as-is; only a literal `== ""` check exists.
- Contract rule it breaks: "Trim leading and trailing spaces on `name`. The trimmed name must be 1-40 characters. Otherwise `400`."

## tests list has no upper bound of 20

- Severity: P2
- Endpoint: `POST /api/runs`
- Steps: `POST` with 21 test names.
- Expected: `400`
- Actual: `201`, all 21 stored.
- Contract rule it breaks: "`tests` must contain 1-20 items. Otherwise `400`." Only the lower bound (`len(tests) == 0`) is checked.

## Individual test names are never trimmed and have no length ceiling

- Severity: P2
- Endpoint: `POST /api/runs`
- Steps: `POST` with `tests: ["  opens  "]` → stored/returned as `"  opens  "`. A 61-character test name is also accepted.
- Expected: each test name trimmed to 1-60 chars post-trim; violations → `400`.
- Actual: no trimming, no length check at all.
- Contract rule it breaks: "Trim each test name. Each trimmed name must be 1-60 characters. Otherwise `400`."

## Duplicate test names are allowed at creation

- Severity: P2
- Endpoint: `POST /api/runs`
- Steps: `POST` with `tests: ["login", "login"]`
- Expected: `400`
- Actual: `201`, both stored, making the second one permanently unaddressable by the results endpoint in any meaningful way (and inflating `total` for summary purposes).
- Contract rule it breaks: "Trimmed test names must be unique. Comparison is case-sensitive... Otherwise `400`."

## duration_ms accepts negative numbers

- Severity: P2
- Endpoint: `POST /api/runs/{id}/results`
- Steps: Submit `{"test": "opens", "status": "pass", "duration_ms": -5}`
- Expected: `400`
- Actual: `200`, `-5` stored and later summed into the summary's `duration_ms`.
- Contract rule it breaks: "`duration_ms` must be an integer greater than or equal to `0`." The store only checks `isinstance(int)` and excludes `bool`; there's no `>= 0` check at all.

## duration_ms: true / false is silently accepted as 1 / 0

- Severity: P2
- Endpoint: `POST /api/runs/{id}/results`
- Steps: Submit `{"test": "opens", "status": "pass", "duration_ms": true}`
- Expected: `400`
- Actual: `200`, stored as `1`.
- Contract rule it breaks: "`true` and `false` are not integers." The store does have an `isinstance(duration_ms, bool)` guard, but it never fires against a real `bool` — Pydantic's `int` field silently coerces the incoming JSON `true`/`false` into a plain `int` (`1`/`0`) before it ever reaches the store, so the type has already changed by the time the guard runs. The guard is dead code as written; the check needs to happen against the raw JSON value, not the post-validation Python value.

## test name isn't trimmed before matching against stored tests

- Severity: P3
- Endpoint: `POST /api/runs/{id}/results`
- Steps: Create a run with test `opens`. Submit a result with `test: "  opens  "`.
- Expected: `200` (matches after trim).
- Actual: `400 {"error": "unknown test"}`.
- Contract rule it breaks: "Trim `test`. It must exactly match one stored test name on that run." No `.strip()` is applied before the membership check.

## status isn't trimmed before the pass/fail/skip check

- Severity: P3
- Endpoint: `POST /api/runs/{id}/results`
- Steps: Submit `status: "  pass  "`.
- Expected: `200`, normalized to `"pass"`.
- Actual: `400 {"error": "status must be pass, fail, or skip"}` — the code only calls `.lower()`, never `.strip()`, so the surrounding whitespace survives into the membership check and fails it.
- Contract rule it breaks: "Normalize `status` by trimming and lowercasing."
