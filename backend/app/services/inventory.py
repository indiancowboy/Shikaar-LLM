"""Inventory store — SQLite-backed (build brief §10, §12).

Durable across restarts (the in-memory MVP lost everything on reload). Uses the
Python stdlib `sqlite3` — no new dependency — and is the brief's stated Phase-2
DB target. The module interface (create/list/get/update/delete/clear) is
unchanged, so routers/services don't care that storage moved under them.

DB path: env `SHIKAAR_DB`, else `backend/data/shikaar.db`. A fresh connection
per call (with CREATE TABLE IF NOT EXISTS) keeps it thread-safe under FastAPI and
lets tests point at an isolated temp DB via the env var.
"""
from __future__ import annotations

import os
import sqlite3
import uuid
from contextlib import contextmanager
from typing import Iterator, Optional

from ..models import FreezerItem, FreezerItemCreate

# backend/data/shikaar.db (this file is backend/app/services/inventory.py)
_DEFAULT_DB = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "shikaar.db"
)

_COLUMNS = (
    "id", "species", "category", "cut", "qty", "unit", "storage",
    "date_frozen", "harvest_location", "notes",
)


def _db_path() -> str:
    return os.environ.get("SHIKAAR_DB", _DEFAULT_DB)


@contextmanager
def _conn() -> Iterator[sqlite3.Connection]:
    path = _db_path()
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    try:
        con.execute(
            """CREATE TABLE IF NOT EXISTS freezer_items (
                id TEXT PRIMARY KEY, species TEXT, category TEXT, cut TEXT,
                qty REAL, unit TEXT, storage TEXT, date_frozen TEXT,
                harvest_location TEXT, notes TEXT
            )"""
        )
        yield con
        con.commit()
    finally:
        con.close()


def _new_id() -> str:
    return "itm_" + uuid.uuid4().hex[:8]


def _row_to_item(r: sqlite3.Row) -> FreezerItem:
    # Pydantic parses the ISO date string back into a date.
    return FreezerItem(**{k: r[k] for k in _COLUMNS})


def _insert(con: sqlite3.Connection, item: FreezerItem) -> None:
    con.execute(
        f"INSERT OR REPLACE INTO freezer_items ({','.join(_COLUMNS)}) "
        f"VALUES ({','.join('?' * len(_COLUMNS))})",
        (
            item.id, item.species, item.category, item.cut, item.qty, item.unit,
            item.storage, item.date_frozen.isoformat(), item.harvest_location, item.notes,
        ),
    )


def create(data: FreezerItemCreate) -> FreezerItem:
    item = FreezerItem(id=_new_id(), **data.model_dump())
    with _conn() as con:
        _insert(con, item)
    return item


def create_many(items: list[FreezerItemCreate]) -> list[FreezerItem]:
    return [create(i) for i in items]


def list_items() -> list[FreezerItem]:
    with _conn() as con:
        rows = con.execute("SELECT * FROM freezer_items").fetchall()
    return [_row_to_item(r) for r in rows]


def get(item_id: str) -> Optional[FreezerItem]:
    with _conn() as con:
        row = con.execute(
            "SELECT * FROM freezer_items WHERE id = ?", (item_id,)
        ).fetchone()
    return _row_to_item(row) if row else None


def update(item_id: str, patch: dict) -> Optional[FreezerItem]:
    """Merge `patch` (validated, unset-excluded) and re-validate before saving."""
    current = get(item_id)
    if current is None:
        return None
    item = FreezerItem(**{**current.model_dump(), **patch})  # raises on invalid merge
    with _conn() as con:
        _insert(con, item)
    return item


def delete(item_id: str) -> bool:
    with _conn() as con:
        cur = con.execute("DELETE FROM freezer_items WHERE id = ?", (item_id,))
        return cur.rowcount > 0


def clear() -> None:
    """Test helper / reset — wipe all rows in the current DB."""
    with _conn() as con:
        con.execute("DELETE FROM freezer_items")
