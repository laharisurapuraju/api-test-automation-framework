"""Test-data builders: valid payloads by default, override only what a test cares about."""
import itertools

_counter = itertools.count(1)


def unique_isbn() -> str:
    """A valid, never-repeated 13-digit ISBN."""
    return f"978{next(_counter):010d}"


def book_payload(**overrides) -> dict:
    payload = {
        "title": "Clean Code",
        "author": "Robert Martin",
        "isbn": unique_isbn(),
        "price": 39.99,
        "stock": 10,
    }
    payload.update(overrides)
    return payload
