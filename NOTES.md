# Notes

## What I tested

- Every rule in the contract for all three endpoints, checked in isolation: `POST /api/runs` (name trimming/length, tests count bounds, per-test trimming/length, uniqueness, sequential ids), `POST /api/runs/{id}/results` (unknown run, test trimming/matching, status trimming/normalization, `duration_ms` type/bound/bool rejection, duplicate rejection), and `GET /api/runs/{id}/summary` (unknown run, `queued`/`running`/`passed`/`failed` status transitions including the "all skipped" edge case, `pass_rate` with and without skips present, `duration_ms` summation, `total`).
- I did not just read the contract and guess what the code does — I ran every scenario against a live `TestClient` first, confirmed the actual behavior, and only then wrote the test. `BUGS.md` reflects verified, reproduced behavior, not inference.
- Generic malformed-body handling (missing field, wrong JSON type) — confirmed this already works correctly via the existing `RequestValidationError` handler, so I didn't file it as a bug, but I kept one boundary test per endpoint for it since it's part of the contract.

## What I did not test, and why

- Concurrency, persistence, auth, and anything requiring a different framework — explicitly out of scope per the assignment.
- I didn't add a test asserting the exact wording of `error` strings, since the assignment says that's not graded — only status code and shape.
- I didn't write a test that pins the *exact* HTTP status FastAPI's own validation handler uses for deeply malformed payloads (e.g. non-JSON body) beyond confirming it's `400` with an `error` key — the contract only asks for that much.
- I did not attempt to test the ordering of the "apply these rules in order" clause for run creation directly (e.g. proving name-length is checked before tests-count), since the current code doesn't implement most of these checks at all yet — there's nothing to sequence. Once the missing validations are added, it'd be worth adding a test for a payload that fails two rules at once, to confirm the first rule in the contract's list wins.

## Where I used AI or other tools

- I used Claude to read the code against the contract, run it live via `TestClient` to confirm every claimed defect empirically (not just from reading), and draft the test files and bug reports. I reviewed the reasoning and reproduction steps for each bug myself before treating anything as confirmed.

## What I would do with more time

- Fix the remaining bugs in `BUGS.md` (I only fixed the `pass_rate` division bug, which also happened to resolve the skip-denominator bug as one line change). The name/test trimming and length validation, duplicate-test-name rejection, duplicate-result rejection, and status normalization at storage time are all small, contained fixes in `store.py`.
- Add a real fix for the `duration_ms: true/false` issue — since Pydantic coerces booleans to ints before the store ever sees them, the check needs to move up to a field validator on `ResultBody` that inspects the raw value, not `isinstance` inside the store.
- Add the missing 404 handling to `store.summary()` (raise `KeyError` like the other two methods do, and let `api.py` catch it the same way `add_result` does) instead of returning a placeholder dict.
- Property-based tests (e.g. with Hypothesis) for the trimming/length/uniqueness rules once they're implemented, since those are exactly the kind of boundary-heavy logic that benefits from generated edge cases.
