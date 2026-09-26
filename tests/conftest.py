import pytest
from fastapi.testclient import TestClient

from testrun.api import app
from testrun.store import store


@pytest.fixture(autouse=True)
def clean_store():
    store.reset()
    yield
    store.reset()


@pytest.fixture
def client():
    return TestClient(app)
