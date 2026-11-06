"""Thin wrapper over requests: base URL, auth header, logging and timing in one place."""
import logging
import time

import requests

log = logging.getLogger("api")


class ApiClient:
    def __init__(self, base_url: str, token: str | None = None, timeout: float = 10.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout
        self.session = requests.Session()
        self.last_elapsed_ms: float = 0.0

    def request(self, method: str, path: str, **kwargs) -> requests.Response:
        headers = kwargs.pop("headers", {})
        if self.token and "Authorization" not in headers:
            headers["Authorization"] = f"Bearer {self.token}"
        started = time.perf_counter()
        response = self.session.request(method, f"{self.base_url}{path}", headers=headers,
                                        timeout=self.timeout, **kwargs)
        self.last_elapsed_ms = (time.perf_counter() - started) * 1000
        log.info("%s %s -> %s (%.0f ms)", method, path, response.status_code, self.last_elapsed_ms)
        return response

    def get(self, path, **kw):
        return self.request("GET", path, **kw)

    def post(self, path, **kw):
        return self.request("POST", path, **kw)

    def put(self, path, **kw):
        return self.request("PUT", path, **kw)

    def delete(self, path, **kw):
        return self.request("DELETE", path, **kw)

    def login(self, username: str, password: str) -> requests.Response:
        response = self.post("/auth/login", json={"username": username, "password": password})
        if response.status_code == 200:
            self.token = response.json()["access_token"]
        return response
