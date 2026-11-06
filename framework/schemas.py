"""JSON Schemas used for contract testing: every response must match its schema."""
BOOK = {
    "type": "object",
    "required": ["id", "title", "author", "isbn", "price", "stock"],
    "additionalProperties": False,
    "properties": {
        "id": {"type": "integer", "minimum": 1},
        "title": {"type": "string", "minLength": 1, "maxLength": 100},
        "author": {"type": "string", "minLength": 1, "maxLength": 100},
        "isbn": {"type": "string", "pattern": "^[0-9]{13}$"},
        "price": {"type": "number", "exclusiveMinimum": 0},
        "stock": {"type": "integer", "minimum": 0},
    },
}

BOOK_LIST = {
    "type": "object",
    "required": ["items", "page", "page_size", "total"],
    "properties": {
        "items": {"type": "array", "items": BOOK},
        "page": {"type": "integer", "minimum": 1},
        "page_size": {"type": "integer", "minimum": 1},
        "total": {"type": "integer", "minimum": 0},
    },
}

TOKEN = {
    "type": "object",
    "required": ["access_token", "token_type", "role"],
    "properties": {
        "access_token": {"type": "string", "minLength": 10},
        "token_type": {"const": "bearer"},
        "role": {"enum": ["admin", "reader"]},
    },
}

ERROR = {"type": "object", "required": ["detail"]}
