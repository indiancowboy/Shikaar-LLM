"""Daily cap on AI actions per user, to keep the OpenAI bill sane.

Counts parse (text), photo parse, meal plan and /ask calls per owner per UTC
day in the same database as the freezer (Postgres in production, SQLite
locally), so the count survives redeploys. Everything else (adding by hand,
Used 1, estimates, Cook First) is unlimited.

AI_DAILY_LIMIT sets the cap (default 20); 0 or less turns it off.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone

from fastapi import Depends, HTTPException

from ..auth import get_owner_id
from . import inventory

DEFAULT_LIMIT = 20

_SQLITE_TABLE = """CREATE TABLE IF NOT EXISTS ai_usage (
    owner_id TEXT NOT NULL, day TEXT NOT NULL, count INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (owner_id, day))"""
_PG_TABLE = """CREATE TABLE IF NOT EXISTS ai_usage (
    owner_id TEXT NOT NULL, day DATE NOT NULL, count INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (owner_id, day))"""


def daily_limit() -> int:
    try:
        return int(os.environ.get("AI_DAILY_LIMIT", DEFAULT_LIMIT))
    except ValueError:
        return DEFAULT_LIMIT


def _today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _increment(owner_id: str, day: str) -> int:
    """Add one use and return the new count (atomic upsert)."""
    if inventory._use_pg():
        from . import inventory_pg

        with inventory_pg._connect() as conn:
            conn.execute(_PG_TABLE)
            row = conn.execute(
                "INSERT INTO ai_usage (owner_id, day, count) VALUES (%s, %s, 1) "
                "ON CONFLICT (owner_id, day) DO UPDATE SET count = ai_usage.count + 1 "
                "RETURNING count",
                (owner_id, day),
            ).fetchone()
            return int(row["count"])

    with inventory._conn() as con:
        con.execute(_SQLITE_TABLE)
        con.execute(
            "INSERT INTO ai_usage (owner_id, day, count) VALUES (?, ?, 1) "
            "ON CONFLICT(owner_id, day) DO UPDATE SET count = count + 1",
            (owner_id, day),
        )
        return con.execute(
            "SELECT count FROM ai_usage WHERE owner_id = ? AND day = ?", (owner_id, day)
        ).fetchone()[0]


def require_ai_quota(owner_id: str = Depends(get_owner_id)) -> None:
    """Route dependency: count this AI action, 429 once over today's limit."""
    limit = daily_limit()
    if limit <= 0:
        return
    if _increment(owner_id, _today()) > limit:
        raise HTTPException(
            status_code=429,
            detail=(
                f"You've used today's {limit} AI actions (parsing, photos, meal plans). "
                "They reset tomorrow. Adding items by hand still works."
            ),
        )


def reset() -> None:
    """Test helper: clear all counts."""
    if inventory._use_pg():
        from . import inventory_pg

        with inventory_pg._connect() as conn:
            conn.execute(_PG_TABLE)
            conn.execute("DELETE FROM ai_usage")
        return
    with inventory._conn() as con:
        con.execute(_SQLITE_TABLE)
        con.execute("DELETE FROM ai_usage")
