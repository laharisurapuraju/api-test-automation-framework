import pytest

from framework import schemas
from framework.assertions import assert_schema, assert_status, assert_validation_error_on
from framework.builders import book_payload


@pytest.mark.regression
@pytest.mark.negative
@pytest.mark.parametrize(
    "field, value",
    [
        ("title", ""), ("title", "x" * 101), ("title", None), ("title", 123),
        ("author", ""), ("author", "x" * 101), ("author", None),
        ("isbn", "123456789012"), ("isbn", "12345678901234"), ("isbn", "97800000000AB"),
        ("isbn", ""), ("isbn", 9780000000001),
        ("price", 0), ("price", -1), ("price", 10000.01), ("price", "free"), ("price", None),
        ("stock", -1), ("stock", 100001), ("stock", "many"), ("stock", 2.5), ("stock", None),
    ],
    ids=lambda v: str(v)[:12] if not isinstance(v, str) or len(v) < 13 else "long-text",
)
def test_invalid_field_values_are_rejected(admin, field, value):
    response = admin.post("/books", json=book_payload(**{field: value}))
    assert_validation_error_on(response, field)
    assert admin.get("/books").json()["total"] == 0  # nothing was stored


@pytest.mark.regression
@pytest.mark.negative
@pytest.mark.parametrize("missing", ["title", "author", "isbn", "price", "stock"])
def test_missing_required_field_is_rejected(admin, missing):
    payload = book_payload()
    del payload[missing]
    assert_validation_error_on(admin.post("/books", json=payload), missing)


@pytest.mark.regression
@pytest.mark.negative
def test_empty_and_malformed_bodies_are_rejected(admin):
    assert_status(admin.post("/books", json={}), 422)
    bad_json = admin.post("/books", data="{not json", headers={"Content-Type": "application/json"})
    assert_status(bad_json, 422)


@pytest.mark.regression
@pytest.mark.parametrize(
    "overrides",
    [{"title": "x"}, {"title": "x" * 100}, {"author": "x" * 100}, {"price": 0.01},
     {"price": 10000}, {"stock": 0}, {"stock": 100000}],
    ids=["title-min", "title-max", "author-max", "price-min", "price-max", "stock-min", "stock-max"],
)
def test_boundary_values_are_accepted(admin, overrides):
    response = admin.post("/books", json=book_payload(**overrides))
    assert_status(response, 201)
    assert_schema(response.json(), schemas.BOOK)


@pytest.mark.regression
def test_unknown_fields_are_ignored_not_stored(admin):
    response = admin.post("/books", json={**book_payload(), "is_admin": True, "discount": 99})
    assert_status(response, 201)
    assert "is_admin" not in response.json() and "discount" not in response.json()


@pytest.mark.regression
@pytest.mark.negative
@pytest.mark.parametrize("title", ["'; DROP TABLE books;--", "<script>alert(1)</script>", "கதை புத்தகம்", "Café ☕ 日本語"],
                         ids=["sql-injection", "html-script", "tamil", "mixed-unicode"])
def test_special_characters_are_stored_literally(admin, title):
    created = admin.post("/books", json=book_payload(title=title))
    assert_status(created, 201)
    assert admin.get(f"/books/{created.json()['id']}").json()["title"] == title
