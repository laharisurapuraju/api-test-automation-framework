import pytest

from framework.assertions import assert_status
from framework.builders import book_payload


@pytest.fixture()
def catalogue(admin):
    """12 books: prices 10, 20 ... 120; authors alternate between Alice and Bob."""
    created = []
    for i in range(1, 13):
        author = "Alice Smith" if i % 2 else "Bob Jones"
        payload = book_payload(title=f"Book {i:02d}", author=author, price=i * 10)
        created.append(admin.post("/books", json=payload).json())
    return created


@pytest.mark.regression
def test_default_page_size_is_ten(admin, catalogue):
    body = admin.get("/books").json()
    assert (body["page"], body["page_size"], body["total"]) == (1, 10, 12)
    assert len(body["items"]) == 10


@pytest.mark.regression
def test_second_page_holds_the_remainder(admin, catalogue):
    body = admin.get("/books", params={"page": 2}).json()
    assert [b["title"] for b in body["items"]] == ["Book 11", "Book 12"]


@pytest.mark.regression
def test_page_beyond_the_end_is_empty_but_total_is_correct(admin, catalogue):
    body = admin.get("/books", params={"page": 99}).json()
    assert body["items"] == [] and body["total"] == 12


@pytest.mark.regression
def test_pages_do_not_overlap_and_cover_everything(admin, catalogue):
    seen = []
    for page in (1, 2, 3, 4):
        seen += [b["id"] for b in admin.get("/books", params={"page": page, "page_size": 5}).json()["items"]]
    assert len(seen) == len(set(seen)) == 12


@pytest.mark.regression
@pytest.mark.negative
@pytest.mark.parametrize("params", [{"page": 0}, {"page": -1}, {"page_size": 0}, {"page_size": 51},
                                    {"page": "abc"}, {"min_price": -1}])
def test_invalid_query_parameters_are_rejected(admin, catalogue, params):
    assert_status(admin.get("/books", params=params), 422)


@pytest.mark.regression
def test_page_size_boundaries_are_accepted(admin, catalogue):
    assert len(admin.get("/books", params={"page_size": 1}).json()["items"]) == 1
    assert len(admin.get("/books", params={"page_size": 50}).json()["items"]) == 12


@pytest.mark.regression
def test_filter_by_author_is_case_insensitive(admin, catalogue):
    body = admin.get("/books", params={"author": "alice smith"}).json()
    assert body["total"] == 6 and {b["author"] for b in body["items"]} == {"Alice Smith"}


@pytest.mark.regression
def test_search_matches_title_or_author(admin, catalogue):
    assert admin.get("/books", params={"q": "book 07"}).json()["total"] == 1
    assert admin.get("/books", params={"q": "BOB"}).json()["total"] == 6
    assert admin.get("/books", params={"q": "no-such-text"}).json()["total"] == 0


@pytest.mark.regression
def test_price_range_is_inclusive(admin, catalogue):
    body = admin.get("/books", params={"min_price": 30, "max_price": 60}).json()
    assert [b["price"] for b in body["items"]] == [30, 40, 50, 60]


@pytest.mark.regression
def test_impossible_price_range_returns_nothing(admin, catalogue):
    assert admin.get("/books", params={"min_price": 90, "max_price": 20}).json()["total"] == 0


@pytest.mark.regression
def test_filters_can_be_combined(admin, catalogue):
    body = admin.get("/books", params={"author": "Bob Jones", "min_price": 50, "max_price": 100}).json()
    assert [b["price"] for b in body["items"]] == [60, 80, 100]
