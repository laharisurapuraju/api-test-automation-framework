"""Fixtures: a live API server, authenticated clients and a clean state per test.

By default the bundled demo API is started on a free port. To test another
deployment instead, set API_BASE_URL (e.g. API_BASE_URL=http://localhost:9000).
"""
import os
import socket
import threading
import time

import pytest
import requests
import uvicorn

from demo_api.app import app
from framework.api_client import ApiClient
from framework.builders import book_payload

ADMIN = ("admin", "Admin@123")
READER = ("reader", "Reader@123")


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def base_url():
    external = os.getenv("API_BASE_URL")
    if external:
        yield external
        return
    port = _free_port()
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{port}"
    for _ in range(100):  # wait until the server answers
        try:
            if requests.get(f"{url}/health", timeout=0.5).ok:
                break
        except requests.ConnectionError:
            time.sleep(0.05)
    else:
        raise RuntimeError("API server did not start")
    yield url
    server.should_exit = True
    thread.join(timeout=5)


def _logged_in(base_url, credentials) -> ApiClient:
    client = ApiClient(base_url)
    assert client.login(*credentials).status_code == 200
    return client


@pytest.fixture(scope="session")
def _admin_session(base_url):
    return _logged_in(base_url, ADMIN)


@pytest.fixture(autouse=True)
def clean_state(_admin_session):
    """Every test starts with an empty catalogue, so tests never depend on each other."""
    assert _admin_session.post("/admin/reset").status_code == 204


@pytest.fixture()
def admin(base_url) -> ApiClient:
    return _logged_in(base_url, ADMIN)


@pytest.fixture()
def reader(base_url) -> ApiClient:
    return _logged_in(base_url, READER)


@pytest.fixture()
def anonymous(base_url) -> ApiClient:
    return ApiClient(base_url)


@pytest.fixture()
def book(admin) -> dict:
    """One book already stored in the catalogue; returns the stored record."""
    response = admin.post("/books", json=book_payload())
    assert response.status_code == 201
    return response.json()
