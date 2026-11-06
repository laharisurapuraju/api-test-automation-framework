import pytest

from framework import schemas
from framework.assertions import assert_schema, assert_status
from framework.builders import book_payload


@pytest.mark.smoke
@pytest.mark.regression
def test_create_book_returns_201_location_and_matching_body(admin):
    payload = book_payload(title="Refactoring", author="Martin Fowler")
    response = admin.post("/books", json=payload)
    assert_status(response, 201)
    body = response.json()
    assert_schema(body, schemas.BOOK)
    assert {k: body[k] for k in payload} == payload  # everything we sent is echoed back
    assert response.headers["Location"] == f"/books/{body['id']}"


@pytest.mark.regression
def test_created_book_can_be_read_back(admin, book):
    response = admin.get(f"/books/{book['id']}")
    assert_status(response, 200)
    assert response.json() == book


@pytest.mark.regression
def test_created_book_appears_in_list(admin, book):
    listing = admin.get("/books").json()
    assert_schema(listing, schemas.BOOK_LIST)
    assert book in listing["items"] and listing["total"] == 1


@pytest.mark.regression
def test_ids_are_assigned_sequentially_and_uniquely(admin):
    ids = [admin.post("/books", json=book_payload()).json()["id"] for _ in range(3)]
    assert ids == sorted(set(ids)) and len(ids) == 3


@pytest.mark.regression
def test_update_replaces_the_book_and_persists(admin, book):
    changed = book_payload(title="Updated title", price=12.5, stock=3, isbn=book["isbn"])
    response = admin.put(f"/books/{book['id']}", json=changed)
    assert_status(response, 200)
    assert_schema(response.json(), schemas.BOOK)
    stored = admin.get(f"/books/{book['id']}").json()
    assert stored == {"id": book["id"], **changed}


@pytest.mark.smoke
@pytest.mark.regression
def test_delete_removes_the_book(admin, book):
    assert_status(admin.delete(f"/books/{book['id']}"), 204)
    assert_status(admin.get(f"/books/{book['id']}"), 404)
    assert admin.get("/books").json()["total"] == 0


@pytest.mark.regression
@pytest.mark.negative
def test_deleting_twice_returns_404_the_second_time(admin, book):
    assert_status(admin.delete(f"/books/{book['id']}"), 204)
    assert_status(admin.delete(f"/books/{book['id']}"), 404)


@pytest.mark.regression
@pytest.mark.negative
@pytest.mark.parametrize("method", ["GET", "PUT", "DELETE"])
def test_unknown_book_id_returns_404(admin, method):
    response = admin.request(method, "/books/99999", json=book_payload() if method == "PUT" else None)
    assert_status(response, 404)
    assert_schema(response.json(), schemas.ERROR)


@pytest.mark.regression
@pytest.mark.negative
@pytest.mark.parametrize("bad_id", ["abc", "1.5", "-"])
def test_non_numeric_book_id_is_a_validation_error(admin, bad_id):
    assert_status(admin.get(f"/books/{bad_id}"), 422)


@pytest.mark.regression
@pytest.mark.negative
def test_duplicate_isbn_is_rejected_with_409(admin, book):
    response = admin.post("/books", json=book_payload(isbn=book["isbn"]))
    assert_status(response, 409)
    assert admin.get("/books").json()["total"] == 1  # nothing extra was stored


@pytest.mark.regression
@pytest.mark.negative
def test_update_cannot_steal_another_books_isbn(admin, book):
    other = admin.post("/books", json=book_payload()).json()
    response = admin.put(f"/books/{other['id']}", json=book_payload(isbn=book["isbn"]))
    assert_status(response, 409)
    assert admin.get(f"/books/{other['id']}").json()["isbn"] == other["isbn"]


@pytest.mark.regression
def test_update_keeping_own_isbn_is_allowed(admin, book):
    response = admin.put(f"/books/{book['id']}", json=book_payload(isbn=book["isbn"], stock=99))
    assert_status(response, 200)
