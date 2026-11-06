"""Bookstore API - the system under test.

Ships inside the repo so the suite is self-contained. It has the features a real
API has that a tester must cover: authentication, roles, validation, filtering,
pagination, uniqueness rules and proper HTTP status codes.
"""
import secrets
from threading import Lock

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Response
from pydantic import BaseModel, Field

app = FastAPI(title="Bookstore API", version="1.0.0")

USERS = {  # username -> (password, role)
    "admin": ("Admin@123", "admin"),
    "reader": ("Reader@123", "reader"),
}
_tokens: dict[str, dict] = {}
_books: dict[int, dict] = {}
_next_id = 1
_lock = Lock()


class LoginRequest(BaseModel):
    username: str
    password: str


class BookIn(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    author: str = Field(min_length=1, max_length=100)
    isbn: str = Field(pattern=r"^\d{13}$")
    price: float = Field(gt=0, le=10000)
    stock: int = Field(ge=0, le=100000)


def current_user(authorization: str = Header(default="")) -> dict:
    scheme, _, token = authorization.partition(" ")
    user = _tokens.get(token) if scheme.lower() == "bearer" else None
    if user is None:
        raise HTTPException(status_code=401, detail="Missing or invalid token",
                            headers={"WWW-Authenticate": "Bearer"})
    return user


def admin_only(user: dict = Depends(current_user)) -> dict:
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")
    return user


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/auth/login")
def login(body: LoginRequest) -> dict:
    record = USERS.get(body.username)
    if record is None or not secrets.compare_digest(record[0], body.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = secrets.token_urlsafe(24)
    _tokens[token] = {"username": body.username, "role": record[1]}
    return {"access_token": token, "token_type": "bearer", "role": record[1]}


@app.post("/admin/reset", status_code=204)
def reset(_: dict = Depends(admin_only)) -> Response:
    """Test-support endpoint: wipes all books so every test starts from a known state."""
    global _next_id
    with _lock:
        _books.clear()
        _next_id = 1
    return Response(status_code=204)


@app.get("/books")
def list_books(
    q: str | None = Query(None, description="case-insensitive match on title or author"),
    author: str | None = None,
    min_price: float | None = Query(None, ge=0),
    max_price: float | None = Query(None, ge=0),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    _: dict = Depends(current_user),
) -> dict:
    items = sorted(_books.values(), key=lambda b: b["id"])
    if q:
        items = [b for b in items if q.lower() in b["title"].lower() or q.lower() in b["author"].lower()]
    if author:
        items = [b for b in items if b["author"].lower() == author.lower()]
    if min_price is not None:
        items = [b for b in items if b["price"] >= min_price]
    if max_price is not None:
        items = [b for b in items if b["price"] <= max_price]
    start = (page - 1) * page_size
    return {"items": items[start:start + page_size], "page": page,
            "page_size": page_size, "total": len(items)}


@app.post("/books", status_code=201)
def create_book(book: BookIn, response: Response, _: dict = Depends(admin_only)) -> dict:
    global _next_id
    with _lock:
        if any(b["isbn"] == book.isbn for b in _books.values()):
            raise HTTPException(status_code=409, detail="A book with this ISBN already exists")
        record = {"id": _next_id, **book.model_dump()}
        _books[_next_id] = record
        _next_id += 1
    response.headers["Location"] = f"/books/{record['id']}"
    return record


@app.get("/books/{book_id}")
def get_book(book_id: int, _: dict = Depends(current_user)) -> dict:
    if book_id not in _books:
        raise HTTPException(status_code=404, detail="Book not found")
    return _books[book_id]


@app.put("/books/{book_id}")
def update_book(book_id: int, book: BookIn, _: dict = Depends(admin_only)) -> dict:
    with _lock:
        if book_id not in _books:
            raise HTTPException(status_code=404, detail="Book not found")
        if any(b["isbn"] == book.isbn and b["id"] != book_id for b in _books.values()):
            raise HTTPException(status_code=409, detail="A book with this ISBN already exists")
        _books[book_id] = {"id": book_id, **book.model_dump()}
        return _books[book_id]


@app.delete("/books/{book_id}", status_code=204)
def delete_book(book_id: int, _: dict = Depends(admin_only)) -> Response:
    with _lock:
        if book_id not in _books:
            raise HTTPException(status_code=404, detail="Book not found")
        del _books[book_id]
    return Response(status_code=204)
