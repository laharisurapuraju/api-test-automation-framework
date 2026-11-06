import pytest

from framework.assertions import assert_status
from framework.builders import book_payload
from tests.conftest import ADMIN


@pytest.mark.smoke
@pytest.mark.regression
def test_full_book_lifecycle(anonymous):
    """login -> create -> read -> update -> list -> delete -> list again."""
    assert_status(anonymous.login(*ADMIN), 200)

    created = anonymous.post("/books", json=book_payload(title="Draft", price=20)).json()
    book_id = created["id"]
    assert anonymous.get(f"/books/{book_id}").json()["title"] == "Draft"

    anonymous.put(f"/books/{book_id}", json=book_payload(isbn=created["isbn"], title="Final", price=25))
    listing = anonymous.get("/books").json()
    assert [(b["title"], b["price"]) for b in listing["items"]] == [("Final", 25)]

    assert_status(anonymous.delete(f"/books/{book_id}"), 204)
    assert anonymous.get("/books").json() == {"items": [], "page": 1, "page_size": 10, "total": 0}


@pytest.mark.regression
def test_data_written_by_admin_is_visible_to_reader(admin, reader):
    created = admin.post("/books", json=book_payload(title="Shared")).json()
    assert reader.get(f"/books/{created['id']}").json()["title"] == "Shared"


@pytest.mark.regression
def test_deleted_book_disappears_for_every_user(admin, reader, book):
    admin.delete(f"/books/{book['id']}")
    assert_status(reader.get(f"/books/{book['id']}"), 404)
