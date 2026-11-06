# API Test Automation Framework

A **REST API test automation framework** built with **Python, Pytest and Requests**. It tests a
Bookstore API that is **bundled in this repo** (FastAPI), so the suite is self-contained and runs the
same way on any machine and in CI.

**106 automated tests** covering authentication, role-based authorization, CRUD behaviour, input
validation and boundary values, search, filtering, pagination, workflows and response times.

## What makes it a framework, not just a test script

| Practice | How it is done here |
|---|---|
| Reusable API client | `framework/api_client.py` adds base URL, bearer token, logging and response timing in one place |
| Test data builders | `framework/builders.py` creates valid payloads with unique ISBNs; tests override only the field they care about |
| Contract testing | Every response is checked against a JSON Schema (`framework/schemas.py`) |
| Readable assertions | `framework/assertions.py` gives clear failure messages (status, schema, field-level validation errors, timing) |
| Test independence | An autouse fixture resets the data before every test, so tests never depend on each other or on order |
| Data-driven testing | `pytest.mark.parametrize` drives validation, boundary and authorization cases |
| Test selection | Markers: `smoke`, `regression`, `negative`, `performance` |
| Reporting | Self-contained HTML report in `reports/report.html` |
| Environment switch | Set `API_BASE_URL` to run the same suite against another deployment |
| CI/CD | GitHub Actions runs the suite on every push and uploads the report |

## Project structure

```
demo_api/app.py         the Bookstore API under test (FastAPI)
framework/              api_client, builders, schemas, assertions
tests/conftest.py       fixtures: live server, admin/reader/anonymous clients, clean state
tests/test_*.py         tests grouped by feature
.github/workflows/      CI pipeline
```

## Setup and run

```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt

pytest                        # all 106 tests
pytest -m smoke               # 8 critical checks
pytest -m negative            # 69 error-handling tests
pytest tests/test_books_validation.py -v
```

Open `reports/report.html` after a run. To explore the API by hand:
`uvicorn demo_api.app:app --reload`, then open http://127.0.0.1:8000/docs
(users: `admin` / `Admin@123`, `reader` / `Reader@123`).

## The API under test

| Endpoint | Rule |
|---|---|
| `POST /auth/login` | returns a bearer token and the user's role |
| `GET /books`, `GET /books/{id}` | any logged-in user; list supports `q`, `author`, `min_price`, `max_price`, `page`, `page_size` |
| `POST /books`, `PUT /books/{id}`, `DELETE /books/{id}` | admin only |
| Validation | title 1-100 chars, author 1-100 chars, ISBN exactly 13 digits, price 0-10000 (exclusive of 0), stock 0-100000 |
| Uniqueness | ISBN must be unique: duplicate gives `409` |

## What is tested

| Area | Examples | Tests |
|---|---|---|
| Authentication | valid/invalid credentials, missing fields, missing/fake/tampered tokens, wrong auth scheme | 21 |
| Authorization | reader can read but not create/update/delete; forbidden calls leave data unchanged; admin-only reset | 7 |
| CRUD | create (201 + Location header), read, update, delete, delete twice, unknown id (404), duplicate ISBN (409) | 16 |
| Validation | invalid values, missing fields, boundary values, malformed JSON, unknown fields, SQL/HTML/Unicode text | 40 |
| Search and pagination | page sizes, last/out-of-range pages, no overlap between pages, filters, inclusive price range, combined filters | 16 |
| Workflows | full create-read-update-delete lifecycle; data visible across users | 3 |
| Performance | login, create/read, full-page listing each under 500 ms | 3 |

## Test approach

- **Boundary value analysis:** each limit is tested just inside and just outside (price `0` and `0.01`,
  title 100 and 101 characters, ISBN 12, 13 and 14 digits).
- **Negative testing first-class:** 69 of the 106 tests check that bad input, missing credentials or
  insufficient permissions are rejected with the right status code and no side effects.
- **State verification:** a rejected request is followed by a read to prove nothing was stored or changed.
- **Suite effectiveness checked:** bugs were deliberately injected into the API (allowing price 0, letting
  readers delete, making the price filter exclusive) and the suite failed each time.

## Possible next steps

- Run in parallel with `pytest-xdist`
- Load testing with Locust
- Run against a deployed environment through `API_BASE_URL`
