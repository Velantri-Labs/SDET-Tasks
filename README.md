# Test Run API

A small service records a test run and summarizes the results. The contract below is the source of truth. The code does not fully follow it.

Your job is to show where.

Time box: **4 hours**. Stop when time is up, even if you are not done. Say what you would do next.

## Setup

Python 3.11 or newer.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest
```

Run the API locally:

```bash
uvicorn testrun.api:app --reload --port 8000
```

`tests/conftest.py` gives you a `client` fixture. The in-memory store resets before each test. Use `fastapi.testclient.TestClient` the same way `tests/test_example.py` does. Keep that example test.

## What to hand in

Work on a branch named `solution/<your-name>` and push it to this repository.

1. **Tests.** Add pytest files under `tests/`. Name each test for the behavior it locks, for example `test_duplicate_result_is_rejected`. Cover success and failure for each endpoint, including boundaries.
2. **`BUGS.md`.** One section per defect you find. Use the template already in that file.
3. **`NOTES.md`.** What you tested, what you left out, and where you used tools or AI.

Assert the contract, not the current behavior. A test that fails on this code is a valid result when the code breaks the contract. Do not weaken a test to make the suite green.

Do not fix every bug. Optional: fix one defect and leave the test that fails without that fix.

## Rules

- AI and docs are allowed. In the follow-up conversation you will explain your tests without reading notes, and you will change one test live.
- Grade your own severity. A crash and a wrong status are not the same kind of defect.
- The wording of `error` strings is not graded. Status codes and response shape are.
- Out of scope: persistence, authentication, concurrency, Docker, and a new framework.

## Pushing your work

```bash
git checkout -b solution/your-name
git add tests BUGS.md NOTES.md
git commit -m "Add API tests and bug reports"
git push -u origin solution/your-name
```

Send the branch link when you are done.

## Contract

Base path: `/api`. Request and response bodies are JSON.

### `POST /api/runs`

Request:

```json
{ "name": "login", "tests": ["opens", "submits"] }
```

Apply these rules in order:

1. Trim leading and trailing spaces on `name`. The trimmed name must be 1–40 characters. Otherwise `400`.
2. `tests` must contain 1–20 items. Otherwise `400`.
3. Trim each test name. Each trimmed name must be 1–60 characters. Otherwise `400`.
4. Trimmed test names must be unique. Comparison is case-sensitive, so `Login` and `login` are different. Otherwise `400`.
5. Store and return the trimmed `name` and the trimmed test names.

Success, `201`:

```json
{
  "id": 1,
  "name": "login",
  "tests": ["opens", "submits"],
  "status": "queued"
}
```

`id` is a positive integer. New runs start at `queued` and have no results.

Error, `400`:

```json
{ "error": "name is required" }
```

### `POST /api/runs/{id}/results`

Request:

```json
{ "test": "opens", "status": "pass", "duration_ms": 12 }
```

1. Unknown run id → `404` and `{ "error": "..." }`.
2. Trim `test`. It must exactly match one stored test name on that run. Otherwise `400`.
3. Normalize `status` by trimming and lowercasing. The only values are `pass`, `fail`, and `skip`. Store the normalized value. Otherwise `400`.
4. `duration_ms` must be an integer greater than or equal to `0`. `true` and `false` are not integers. Otherwise `400`.
5. Each test accepts one result. A second result for the same test → `400`, and the first result stays as it was.

Success, `200`:

```json
{ "id": 1, "test": "opens", "status": "pass", "duration_ms": 12 }
```

`status` in this body is the normalized value.

### `GET /api/runs/{id}/summary`

Unknown run id → `404` and `{ "error": "..." }`.

Success, `200`:

```json
{
  "id": 1,
  "name": "login",
  "status": "running",
  "total": 2,
  "passed": 1,
  "failed": 0,
  "skipped": 0,
  "pass_rate": 1.0,
  "duration_ms": 12
}
```

- `total` is the number of tests on the run.
- `passed`, `failed`, and `skipped` count stored results after status normalization.
- `duration_ms` is the sum of stored durations.
- `pass_rate` is `passed / (passed + failed)`. Skips are not part of that ratio. When `passed + failed` is `0`, `pass_rate` is `0.0`. This endpoint does not return an error for that case.
- `status` is exactly one of:
  - `queued` when the run has no results
  - `failed` when at least one result is `fail`, even if other tests have no result yet
  - `passed` when every test has a result and none of them is `fail`
  - `running` when at least one result is in, none is `fail`, and at least one test has no result yet

A body that is missing fields, or is the wrong JSON type, is `400` with an `error` key. You do not have to assert the exact text.
