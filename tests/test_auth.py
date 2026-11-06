import pytest

from framework import schemas
from framework.assertions import assert_schema, assert_status
from tests.conftest import ADMIN, READER


@pytest.mark.smoke
@pytest.mark.regression
@pytest.mark.parametrize("credentials, role", [(ADMIN, "admin"), (READER, "reader")])
def test_valid_login_returns_token_and_role(anonymous, credentials, role):
    response = anonymous.login(*credentials)
    assert_status(response, 200)
    assert_schema(response.json(), schemas.TOKEN)
    assert response.json()["role"] == role


@pytest.mark.regression
@pytest.mark.negative
@pytest.mark.parametrize(
    "username, password",
    [("admin", "wrong"), ("nobody", "Admin@123"), ("", ""), ("admin", ""), ("ADMIN", "Admin@123")],
    ids=["wrong-password", "unknown-user", "both-empty", "empty-password", "username-is-case-sensitive"],
)
def test_invalid_credentials_are_rejected(anonymous, username, password):
    response = anonymous.login(username, password)
    assert_status(response, 401)
    assert_schema(response.json(), schemas.ERROR)
    assert "access_token" not in response.text  # never leak a token on failure


@pytest.mark.regression
@pytest.mark.negative
@pytest.mark.parametrize("body", [{}, {"username": "admin"}, {"password": "Admin@123"}],
                         ids=["empty", "no-password", "no-username"])
def test_login_with_missing_fields_is_a_validation_error(anonymous, body):
    assert_status(anonymous.post("/auth/login", json=body), 422)


@pytest.mark.regression
@pytest.mark.negative
@pytest.mark.parametrize(
    "method, path",
    [("GET", "/books"), ("GET", "/books/1"), ("POST", "/books"), ("PUT", "/books/1"),
     ("DELETE", "/books/1")],
)
def test_endpoints_require_authentication(anonymous, method, path):
    response = anonymous.request(method, path, json={} if method in ("POST", "PUT") else None)
    assert_status(response, 401)
    assert response.headers.get("WWW-Authenticate") == "Bearer"


@pytest.mark.regression
@pytest.mark.negative
@pytest.mark.parametrize(
    "header",
    ["Bearer not-a-real-token", "Bearer ", "Basic YWRtaW46QWRtaW5AMTIz", "token-without-scheme"],
    ids=["fake-token", "empty-token", "wrong-scheme", "no-scheme"],
)
def test_invalid_authorization_headers_are_rejected(anonymous, header):
    assert_status(anonymous.get("/books", headers={"Authorization": header}), 401)


@pytest.mark.regression
def test_tampered_token_is_rejected(admin):
    admin.token = admin.token[:-1] + ("A" if admin.token[-1] != "A" else "B")
    assert_status(admin.get("/books"), 401)


@pytest.mark.regression
def test_each_login_issues_a_different_token(anonymous):
    first = anonymous.login(*ADMIN).json()["access_token"]
    second = anonymous.login(*ADMIN).json()["access_token"]
    assert first != second
