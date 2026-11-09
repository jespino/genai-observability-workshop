"""The tools the agent can use, and their descriptions for the model."""

import random
import time

CATALOG = [
    {"id": "bk-001", "title": "The Trace of Time", "author": "Ada Lindqvist"},
    {"id": "bk-002", "title": "Spans of Control", "author": "Marcus Oyelaran"},
    {"id": "bk-003", "title": "A Field Guide to Logs", "author": "Ines Duarte"},
    {"id": "bk-004", "title": "Cardinality Explosion", "author": "Tomas Reiter"},
    {"id": "bk-005", "title": "The Sampling Paradox", "author": "Priya Raman"},
]

STOCK = {"bk-001": 12, "bk-002": 3, "bk-003": 0, "bk-005": 7}


class WarehouseTimeout(Exception):
    pass


def search_books(query):
    words = [word.lower().strip("?.,!") for word in query.split()]
    words = [word for word in words if len(word) > 3]
    found = [
        book
        for book in CATALOG
        if any(word in f"{book['title']} {book['author']}".lower() for word in words)
    ]
    return {"books": found}


def check_stock(book_id):
    if book_id == "bk-004":
        time.sleep(1.5)
        raise WarehouseTimeout(f"warehouse did not answer for {book_id}")
    time.sleep(random.uniform(0.05, 0.2))
    return {"book_id": book_id, "copies": STOCK.get(book_id, 0)}


FUNCTIONS = {"search_books": search_books, "check_stock": check_stock}

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_books",
            "description": "Search the catalog by title or author.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_stock",
            "description": "Get the copies in stock of a book, by its id.",
            "parameters": {
                "type": "object",
                "properties": {"book_id": {"type": "string"}},
                "required": ["book_id"],
            },
        },
    },
]
