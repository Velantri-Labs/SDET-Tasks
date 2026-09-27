def test_list_runs_empty(client):
    response = client.get("/api/runs")

    assert response.status_code == 200
    assert response.json() == []


def test_list_runs_after_two_creates(client):
    first = client.post(
        "/api/runs",
        json={"name": "login", "tests": ["opens", "submits"]},
    )
    second = client.post(
        "/api/runs",
        json={"name": "checkout", "tests": ["pay", "confirm", "receipt"]},
    )
    assert first.status_code == 201
    assert second.status_code == 201

    response = client.get("/api/runs")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2

    # Newest run first.
    assert body[0] == {
        "id": second.json()["id"],
        "name": "checkout",
        "status": "queued",
        "total": 3,
        "pass_rate": 0.0,
        "tests": ["pay", "confirm", "receipt"],
    }
    assert body[1] == {
        "id": first.json()["id"],
        "name": "login",
        "status": "queued",
        "total": 2,
        "pass_rate": 0.0,
        "tests": ["opens", "submits"],
    }


def test_list_runs_reflects_status_and_pass_rate(client):
    created = client.post(
        "/api/runs",
        json={"name": "login", "tests": ["opens", "submits"]},
    )
    run_id = created.json()["id"]

    client.post(
        f"/api/runs/{run_id}/results",
        json={"test": "opens", "status": "pass", "duration_ms": 10},
    )

    response = client.get("/api/runs")
    body = response.json()

    assert len(body) == 1
    assert body[0]["status"] == "running"
    assert body[0]["pass_rate"] == 1.0
