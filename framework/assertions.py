"""Readable assertion helpers that give useful failure messages."""
import jsonschema


def assert_status(response, expected: int) -> None:
    assert response.status_code == expected, (
        f"Expected HTTP {expected} but got {response.status_code}. Body: {response.text[:300]}"
    )


def assert_schema(data, schema: dict) -> None:
    try:
        jsonschema.validate(data, schema)
    except jsonschema.ValidationError as exc:
        raise AssertionError(f"Response does not match schema: {exc.message} (at {list(exc.path)})") from exc


def assert_fast(client, limit_ms: float) -> None:
    assert client.last_elapsed_ms <= limit_ms, (
        f"Response took {client.last_elapsed_ms:.0f} ms, limit is {limit_ms:.0f} ms"
    )


def assert_validation_error_on(response, field: str) -> None:
    """A 422 whose error details point at the offending field."""
    assert_status(response, 422)
    locations = [".".join(str(p) for p in err["loc"]) for err in response.json()["detail"]]
    assert any(loc.endswith(field) for loc in locations), f"No error reported for '{field}': {locations}"
