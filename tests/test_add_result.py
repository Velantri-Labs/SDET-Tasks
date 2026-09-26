def make_run(client, tests=("opens", "submits")):
    response = client.post(
        "/api/runs",
        json={"name": "login", "tests": list(tests)},
    )
    return response.json()["id"]


def test_add_result_unknown_run_returns_404(client):
    response = client.post(
        "/api/runs/999/results",
        json={"test": "opens", "status": "pass", "duration_ms": 12},
    )

    assert response.status_code == 404
    assert "error" in response.json()


def test_add_result_success_returns_normalized_status_and_shape(client):
    run_id = make_run(client)

    response = client.post(
        f"/api/runs/{run_id}/results",
        json={"test": "opens", "status": "pass", "duration_ms": 12},
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": run_id,
        "test": "opens",
        "status": "pass",
        "duration_ms": 12,
    }


def test_add_result_rejects_unmatched_test(client):
    run_id = make_run(client)

    response = client.post(
        f"/api/runs/{run_id}/results",
        json={"test": "does-not-exist", "status": "pass", "duration_ms": 12},
    )

    assert response.status_code == 400


def test_add_result_trims_test_name_before_matching(client):
    run_id = make_run(client)

    response = client.post(
        f"/api/runs/{run_id}/results",
        json={"test": "  opens  ", "status": "pass", "duration_ms": 12},
    )

    assert response.status_code == 200
    assert response.json()["test"] == "opens"


def test_add_result_normalizes_status_case_and_whitespace(client):
    run_id = make_run(client)

    response = client.post(
        f"/api/runs/{run_id}/results",
        json={"test": "opens", "status": "  PASS  ", "duration_ms": 12},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "pass"


def test_add_result_normalized_status_is_reflected_in_summary_counts(client):
    run_id = make_run(client, tests=("opens",))

    client.post(
        f"/api/runs/{run_id}/results",
        json={"test": "opens", "status": "PASS", "duration_ms": 12},
    )

    summary = client.get(f"/api/runs/{run_id}/summary").json()
    assert summary["passed"] == 1


def test_add_result_rejects_invalid_status(client):
    run_id = make_run(client)

    response = client.post(
        f"/api/runs/{run_id}/results",
        json={"test": "opens", "status": "broken", "duration_ms": 12},
    )

    assert response.status_code == 400


def test_add_result_accepts_zero_duration(client):
    run_id = make_run(client)

    response = client.post(
        f"/api/runs/{run_id}/results",
        json={"test": "opens", "status": "pass", "duration_ms": 0},
    )

    assert response.status_code == 200


def test_add_result_rejects_negative_duration(client):
    run_id = make_run(client)

    response = client.post(
        f"/api/runs/{run_id}/results",
        json={"test": "opens", "status": "pass", "duration_ms": -1},
    )

    assert response.status_code == 400


def test_add_result_rejects_non_integer_duration(client):
    run_id = make_run(client)

    response = client.post(
        f"/api/runs/{run_id}/results",
        json={"test": "opens", "status": "pass", "duration_ms": 12.5},
    )

    assert response.status_code == 400


def test_add_result_rejects_boolean_true_duration(client):
    run_id = make_run(client)

    response = client.post(
        f"/api/runs/{run_id}/results",
        json={"test": "opens", "status": "pass", "duration_ms": True},
    )

    assert response.status_code == 400


def test_add_result_rejects_boolean_false_duration(client):
    run_id = make_run(client)

    response = client.post(
        f"/api/runs/{run_id}/results",
        json={"test": "opens", "status": "pass", "duration_ms": False},
    )

    assert response.status_code == 400


def test_add_result_rejects_duplicate_result_for_same_test(client):
    run_id = make_run(client, tests=("opens",))

    client.post(
        f"/api/runs/{run_id}/results",
        json={"test": "opens", "status": "pass", "duration_ms": 12},
    )
    second = client.post(
        f"/api/runs/{run_id}/results",
        json={"test": "opens", "status": "fail", "duration_ms": 5},
    )

    assert second.status_code == 400


def test_add_result_duplicate_attempt_does_not_change_first_result(client):
    run_id = make_run(client, tests=("opens",))

    client.post(
        f"/api/runs/{run_id}/results",
        json={"test": "opens", "status": "pass", "duration_ms": 12},
    )
    client.post(
        f"/api/runs/{run_id}/results",
        json={"test": "opens", "status": "fail", "duration_ms": 5},
    )

    summary = client.get(f"/api/runs/{run_id}/summary").json()
    assert summary["passed"] == 1
    assert summary["failed"] == 0
    assert summary["duration_ms"] == 12


def test_add_result_rejects_missing_status_field(client):
    run_id = make_run(client)

    response = client.post(
        f"/api/runs/{run_id}/results",
        json={"test": "opens", "duration_ms": 12},
    )

    assert response.status_code == 400
    assert "error" in response.json()
