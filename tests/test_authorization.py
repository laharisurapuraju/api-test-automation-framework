import pytest

from framework.assertions import assert_status
from framework.builders import book_payload


@pytest.mark.regression
def test_reader_can_read(reader, book):
    assert_status(reader.get("/books"), 200)
    assert_status(reader.get(f"/books/{book['id']}"), 200)


@pytest.mark.smoke
@pytest.mark.regression
@pytest.mark.negative
@pytest.mark.parametrize("method, path, body", [
    ("POST", "/books", "new"), ("PUT", "/books/{id}", "new"), ("DELETE", "/books/{id}", None),
], ids=["create", "update", "delete"])
def test_reader_cannot_modify_data(reader, book, method, path, body):
    payload = book_payload() if body else None
    response = reader.request(method, path.format(id=book["id"]), json=payload)
    assert_status(response, 403)


@pytest.mark.regression
@pytest.mark.negative
def test_forbidden_requests_leave_data_unchanged(admin, reader, book):
    reader.delete(f"/books/{book['id']}")
    reader.put(f"/books/{book['id']}", json=book_payload(title="Hacked"))
    assert admin.get(f"/books/{book['id']}").json() == book


@pytest.mark.regression
@pytest.mark.negative
def test_reader_cannot_use_the_admin_reset_endpoint(reader, admin, book):
    assert_status(reader.post("/admin/reset"), 403)
    assert admin.get("/books").json()["total"] == 1


@pytest.mark.regression
def test_admin_can_perform_every_operation(admin):
    created = admin.post("/books", json=book_payload())
    assert_status(created, 201)
    book_id = created.json()["id"]
    assert_status(admin.put(f"/books/{book_id}", json=book_payload(isbn=created.json()["isbn"])), 200)
    assert_status(admin.delete(f"/books/{book_id}"), 204)
