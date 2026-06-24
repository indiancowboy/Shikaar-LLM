"""Inventory store — SQLite-backed, scoped per client (build brief §10, §12).

Each browser sends an `X-Client-Id` header (see app/security.py get_client_id);
every row is tagged with it and all reads/writes are filtered by it, so testers
get private freezers without accounts. Requests with no client id fall into a
shared "shared" bucket.

Durable across restarts (stdlib sqlite3). DB path: env `SHIKAAR_DB`, else
`backend/data/shikaar.db`. Fresh connection per call keeps it thread-safe under
FastAPI and lets tests point at an isolated temp DB.
"""
from __future__ import annotations

import os
import sqlite3
import uuid
from contextlib import contextmanager
from typing import Iterator, Optional

from ..models import FreezerItem, FreezerItemCreate

_DEFAULT_DB = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "shikaar.db"
)

# FreezerItem fields (client_id is stored alongside but is not a model field).
_ITEM_COLUMNS = (
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
                id TEXT PRIMARY KEY, client_id TEXT, species TEXT, category TEXT,
                cut TEXT, qty REAL, unit TEXT, storage TEXT, date_frozen TEXT,
                harvest_location TEXT, notes TEXT
            )"""
        )
        # Migrate older DBs that predate the client_id column.
        cols = [r[1] for r in con.execute("PRAGMA table_info(freezer_items)")]
        if "client_id" not in cols:
            con.execute("ALTER TABLE freezer_items ADD COLUMN client_id TEXT")
        yield con
        con.commit()
    finally:
        con.close()


def _new_id() -> str:
    return "itm_" + uuid.uuid4().hex[:8]


def _row_to_item(r: sqlite3.Row) -> FreezerItem:
    return FreezerItem(**{k: r[k] for k in _ITEM_COLUMNS})


def _insert(con: sqlite3.Connection, item: FreezerItem, client_id: str) -> None:
    con.execute(
        f"INSERT OR REPLACE INTO freezer_items (client_id,{','.join(_ITEM_COLUMNS)}) "
        f"VALUES ({','.join('?' * (len(_ITEM_COLUMNS) + 1))})",
        (
            client_id, item.id, item.species, item.category, item.cut, item.qty,
            item.unit, item.storage, item.date_frozen.isoformat(),
            item.harvest_location, item.notes,
        ),
    )


def create(data: FreezerItemCreate, client_id: str) -> FreezerItem:
    item = FreezerItem(id=_new_id(), **data.model_dump())
    with _conn() as con:
        _insert(con, item, client_id)
    return item


def create_many(items: list[FreezerItemCreate], client_id: str) -> list[FreezerItem]:
    return [create(i, client_id) for i in items]


def list_items(client_id: str) -> list[FreezerItem]:
    with _conn() as con:
        rows = con.execute(
            "SELECT * FROM freezer_items WHERE client_id = ?", (client_id,)
        ).fetchall()
    return [_row_to_item(r) for r in rows]


def get(item_id: str, client_id: str) -> Optional[FreezerItem]:
    with _conn() as con:
        row = con.execute(
            "SELECT * FROM freezer_items WHERE id = ? AND client_id = ?",
            (item_id, client_id),
        ).fetchone()
    return _row_to_item(row) if row else None


def update(item_id: str, patch: dict, client_id: str) -> Optional[FreezerItem]:
    """Merge `patch` (validated, unset-excluded) and re-validate. Scoped to the
    owner so one client can't edit another's items."""
    current = get(item_id, client_id)
    if current is None:
        return None
    item = FreezerItem(**{**current.model_dump(), **patch})  # raises on invalid merge
    with _conn() as con:
        _insert(con, item, client_id)
    return item


def delete(item_id: str, client_id: str) -> bool:
    with _conn() as con:
        cur = con.execute(
            "DELETE FROM freezer_items WHERE id = ? AND client_id = ?",
            (item_id, client_id),
        )
        return cur.rowcount > 0


def clear(client_id: Optional[str] = None) -> None:
    """Test helper / reset. Clears one client's rows, or all if client_id is None."""
    with _conn() as con:
        if client_id is None:
            con.execute("DELETE FROM freezer_items")
        else:
            con.execute("DELETE FROM freezer_items WHERE client_id = ?", (client_id,))
