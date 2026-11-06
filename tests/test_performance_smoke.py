"""Basic response-time guard rails. These are smoke checks, not load tests."""
import pytest

from framework.assertions import assert_fast, assert_status
from framework.builders import book_payload

LIMIT_MS = 500


@pytest.mark.performance
def test_login_is_fast(anonymous):
    assert_status(anonymous.login("admin", "Admin@123"), 200)
    assert_fast(anonymous, LIMIT_MS)


@pytest.mark.performance
def test_create_and_read_are_fast(admin):
    created = admin.post("/books", json=book_payload())
    assert_fast(admin, LIMIT_MS)
    admin.get(f"/books/{created.json()['id']}")
    assert_fast(admin, LIMIT_MS)


@pytest.mark.performance
def test_listing_stays_fast_with_a_full_page_of_data(admin):
    for _ in range(50):
        admin.post("/books", json=book_payload())
    assert_status(admin.get("/books", params={"page_size": 50}), 200)
    assert_fast(admin, LIMIT_MS)
