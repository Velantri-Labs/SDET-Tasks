def test_create_run_returns_queued(client):
    response = client.post(
        "/api/runs",
        json={"name": "login", "tests": ["opens", "submits"]},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1
    assert body["name"] == "login"
    assert body["tests"] == ["opens", "submits"]
    assert body["status"] == "queued"
