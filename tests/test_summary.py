def make_run(client, tests):
    response = client.post(
        "/api/runs",
        json={"name": "login", "tests": list(tests)},
    )
    return response.json()["id"]


def add_result(client, run_id, test, status, duration_ms):
    return client.post(
        f"/api/runs/{run_id}/results",
        json={"test": test, "status": status, "duration_ms": duration_ms},
    )


def test_summary_unknown_run_returns_404(client):
    response = client.get("/api/runs/999/summary")

    assert response.status_code == 404
    assert "error" in response.json()


def test_summary_freshly_created_run_does_not_error(client):
    run_id = make_run(client, ["opens"])

    response = client.get(f"/api/runs/{run_id}/summary")

    assert response.status_code == 200


def test_summary_freshly_created_run_is_queued(client):
    run_id = make_run(client, ["opens"])

    summary = client.get(f"/api/runs/{run_id}/summary").json()

    assert summary["status"] == "queued"
    assert summary["total"] == 1
    assert summary["passed"] == 0
    assert summary["failed"] == 0
    assert summary["skipped"] == 0


def test_summary_zero_results_pass_rate_is_zero(client):
    run_id = make_run(client, ["opens"])

    summary = client.get(f"/api/runs/{run_id}/summary").json()

    assert summary["pass_rate"] == 0.0


def test_summary_is_running_when_some_tests_still_pending(client):
    run_id = make_run(client, ["opens", "submits"])
    add_result(client, run_id, "opens", "pass", 12)

    summary = client.get(f"/api/runs/{run_id}/summary").json()

    # This is the exact scenario worked through in the contract's own example.
    assert summary["status"] == "running"
    assert summary["total"] == 2
    assert summary["passed"] == 1


def test_summary_is_passed_only_once_every_test_has_a_result(client):
    run_id = make_run(client, ["opens", "submits"])
    add_result(client, run_id, "opens", "pass", 12)
    add_result(client, run_id, "submits", "pass", 8)

    summary = client.get(f"/api/runs/{run_id}/summary").json()

    assert summary["status"] == "passed"


def test_summary_is_failed_when_any_result_is_fail_even_with_pending_tests(client):
    run_id = make_run(client, ["opens", "submits"])
    add_result(client, run_id, "opens", "fail", 12)

    summary = client.get(f"/api/runs/{run_id}/summary").json()

    assert summary["status"] == "failed"


def test_summary_all_tests_skipped_and_complete_is_passed(client):
    run_id = make_run(client, ["opens", "submits"])
    add_result(client, run_id, "opens", "skip", 0)
    add_result(client, run_id, "submits", "skip", 0)

    summary = client.get(f"/api/runs/{run_id}/summary").json()

    # No fail present and every test has a result, so per contract this
    # is "passed" even though nothing actually passed.
    assert summary["status"] == "passed"
    assert summary["pass_rate"] == 0.0


def test_summary_pass_rate_excludes_skips_from_denominator(client):
    run_id = make_run(client, ["a", "b"])
    add_result(client, run_id, "a", "pass", 10)
    add_result(client, run_id, "b", "skip", 0)

    summary = client.get(f"/api/runs/{run_id}/summary").json()

    assert summary["pass_rate"] == 1.0


def test_summary_duration_ms_sums_stored_durations(client):
    run_id = make_run(client, ["a", "b"])
    add_result(client, run_id, "a", "pass", 10)
    add_result(client, run_id, "b", "fail", 15)

    summary = client.get(f"/api/runs/{run_id}/summary").json()

    assert summary["duration_ms"] == 25


def test_summary_total_equals_number_of_tests_on_run(client):
    run_id = make_run(client, ["a", "b", "c"])

    summary = client.get(f"/api/runs/{run_id}/summary").json()

    assert summary["total"] == 3
