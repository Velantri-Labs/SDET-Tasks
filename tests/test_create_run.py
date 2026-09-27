def test_create_run_trims_name_whitespace(client):
    response = client.post(
        "/api/runs",
        json={"name": "  login  ", "tests": ["opens"]},
    )

    assert response.status_code == 201
    assert response.json()["name"] == "login"


def test_create_run_rejects_empty_name(client):
    response = client.post(
        "/api/runs",
        json={"name": "", "tests": ["opens"]},
    )

    assert response.status_code == 400
    assert "error" in response.json()


def test_create_run_rejects_whitespace_only_name(client):
    response = client.post(
        "/api/runs",
        json={"name": "    ", "tests": ["opens"]},
    )

    assert response.status_code == 400


def test_create_run_accepts_name_at_max_length(client):
    response = client.post(
        "/api/runs",
        json={"name": "x" * 40, "tests": ["opens"]},
    )

    assert response.status_code == 201
    assert response.json()["name"] == "x" * 40


def test_create_run_rejects_name_over_max_length(client):
    response = client.post(
        "/api/runs",
        json={"name": "x" * 41, "tests": ["opens"]},
    )

    assert response.status_code == 400


def test_create_run_rejects_empty_tests_list(client):
    response = client.post(
        "/api/runs",
        json={"name": "login", "tests": []},
    )

    assert response.status_code == 400


def test_create_run_accepts_tests_at_max_count(client):
    response = client.post(
        "/api/runs",
        json={"name": "login", "tests": [f"t{i}" for i in range(20)]},
    )

    assert response.status_code == 201
    assert len(response.json()["tests"]) == 20


def test_create_run_rejects_tests_over_max_count(client):
    response = client.post(
        "/api/runs",
        json={"name": "login", "tests": [f"t{i}" for i in range(21)]},
    )

    assert response.status_code == 400


def test_create_run_trims_each_test_name(client):
    response = client.post(
        "/api/runs",
        json={"name": "login", "tests": ["  opens  ", "submits"]},
    )

    assert response.status_code == 201
    assert response.json()["tests"] == ["opens", "submits"]


def test_create_run_rejects_test_name_empty_after_trim(client):
    response = client.post(
        "/api/runs",
        json={"name": "login", "tests": ["   "]},
    )

    assert response.status_code == 400


def test_create_run_accepts_test_name_at_max_length(client):
    response = client.post(
        "/api/runs",
        json={"name": "login", "tests": ["t" * 60]},
    )

    assert response.status_code == 201


def test_create_run_rejects_test_name_over_max_length(client):
    response = client.post(
        "/api/runs",
        json={"name": "login", "tests": ["t" * 61]},
    )

    assert response.status_code == 400


def test_create_run_rejects_duplicate_test_names_case_sensitive(client):
    response = client.post(
        "/api/runs",
        json={"name": "login", "tests": ["login", "login"]},
    )

    assert response.status_code == 400


def test_create_run_allows_test_names_differing_only_by_case(client):
    response = client.post(
        "/api/runs",
        json={"name": "login", "tests": ["Login", "login"]},
    )

    assert response.status_code == 201
    assert response.json()["tests"] == ["Login", "login"]


def test_create_run_rejects_duplicate_test_names_after_trimming(client):
    # "opens" and "opens " are the same trimmed name, so this must be
    # rejected even though the raw strings differ.
    response = client.post(
        "/api/runs",
        json={"name": "login", "tests": ["opens", "opens "]},
    )

    assert response.status_code == 400


def test_create_run_returns_positive_sequential_ids(client):
    first = client.post("/api/runs", json={"name": "a", "tests": ["t"]})
    second = client.post("/api/runs", json={"name": "b", "tests": ["t"]})

    assert first.json()["id"] == 1
    assert second.json()["id"] == 2


def test_create_run_rejects_wrong_type_for_tests(client):
    response = client.post(
        "/api/runs",
        json={"name": "login", "tests": "opens"},
    )

    assert response.status_code == 400
    assert "error" in response.json()


def test_create_run_rejects_missing_name_field(client):
    response = client.post(
        "/api/runs",
        json={"tests": ["opens"]},
    )

    assert response.status_code == 400
    assert "error" in response.json()
