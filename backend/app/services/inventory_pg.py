"""Postgres-backed inventory store (durable, for accounts-mode deploys).

Mirrors the function signatures of ``inventory`` (the SQLite store) exactly, so
``inventory`` can delegate here when ``DATABASE_URL`` is set. Rows are scoped by
``owner_id`` — the Supabase user id in accounts mode — so a freezer persists
across redeploys and follows the user across devices.

Connection per call (psycopg handles pooling at the driver level well enough for
this scale) keeps it thread-safe under FastAPI. The table is created on demand.
"""
from __future__ import annotations

import os
from typing import Optional

from ..models import FreezerItem, FreezerItemCreate
from .inventory import _ITEM_COLUMNS, _new_id  # reuse column list + id scheme

_CREATE_SQL = """
CREATE TABLE IF NOT EXISTS freezer_items (
    id TEXT PRIMARY KEY,
    owner_id TEXT NOT NULL,
    species TEXT,
    category TEXT,
    cut TEXT,
    qty DOUBLE PRECISION,
    unit TEXT,
    storage TEXT,
    date_frozen DATE,
    harvest_location TEXT,
    notes TEXT,
    packs INTEGER,
    pack_size DOUBLE PRECISION
);
CREATE INDEX IF NOT EXISTS freezer_items_owner_idx ON freezer_items (owner_id);
-- Tables created before packs existed (e.g. the live one) gain the columns here.
ALTER TABLE freezer_items ADD COLUMN IF NOT EXISTS packs INTEGER;
ALTER TABLE freezer_items ADD COLUMN IF NOT EXISTS pack_size DOUBLE PRECISION;
"""


def _dsn() -> str:
    return os.environ["DATABASE_URL"]


def _connect():
    import psycopg
    from psycopg.rows import dict_row

    conn = psycopg.connect(_dsn(), row_factory=dict_row, autocommit=True)
    conn.execute(_CREATE_SQL)
    return conn


def _row_to_item(r: dict) -> FreezerItem:
    return FreezerItem(**{k: r[k] for k in _ITEM_COLUMNS})


def _upsert(conn, item: FreezerItem, owner_id: str) -> None:
    cols = ("owner_id",) + _ITEM_COLUMNS
    placeholders = ", ".join(["%s"] * len(cols))
    updates = ", ".join(f"{c} = EXCLUDED.{c}" for c in cols if c != "id")
    conn.execute(
        f"INSERT INTO freezer_items ({', '.join(cols)}) VALUES ({placeholders}) "
        f"ON CONFLICT (id) DO UPDATE SET {updates}",
        (
            owner_id, item.id, item.species, item.category, item.cut, item.qty,
            item.unit, item.storage, item.date_frozen, item.harvest_location,
            item.notes, item.packs, item.pack_size,
        ),
    )


def create(data: FreezerItemCreate, owner_id: str) -> FreezerItem:
    item = FreezerItem(id=_new_id(), **data.model_dump())
    with _connect() as conn:
        _upsert(conn, item, owner_id)
    return item


def create_many(items: list[FreezerItemCreate], owner_id: str) -> list[FreezerItem]:
    return [create(i, owner_id) for i in items]


def list_items(owner_id: str) -> list[FreezerItem]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM freezer_items WHERE owner_id = %s", (owner_id,)
        ).fetchall()
    return [_row_to_item(r) for r in rows]


def get(item_id: str, owner_id: str) -> Optional[FreezerItem]:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM freezer_items WHERE id = %s AND owner_id = %s",
            (item_id, owner_id),
        ).fetchone()
    return _row_to_item(row) if row else None


def update(item_id: str, patch: dict, owner_id: str) -> Optional[FreezerItem]:
    current = get(item_id, owner_id)
    if current is None:
        return None
    item = FreezerItem(**{**current.model_dump(), **patch})  # re-validates
    with _connect() as conn:
        _upsert(conn, item, owner_id)
    return item


def delete(item_id: str, owner_id: str) -> bool:
    with _connect() as conn:
        cur = conn.execute(
            "DELETE FROM freezer_items WHERE id = %s AND owner_id = %s",
            (item_id, owner_id),
        )
        return cur.rowcount > 0


def clear(owner_id: Optional[str] = None) -> None:
    with _connect() as conn:
        if owner_id is None:
            conn.execute("DELETE FROM freezer_items")
        else:
            conn.execute("DELETE FROM freezer_items WHERE owner_id = %s", (owner_id,))
