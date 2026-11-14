"""Postgres connection pool + one-time schema setup (needs a test database)."""
from __future__ import annotations

import os
from datetime import date

import pytest

_TEST_DB = os.environ.get("SHIKAAR_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not _TEST_DB, reason="set SHIKAAR_TEST_DATABASE_URL to run Postgres tests")


def test_schema_runs_once_and_pool_is_reused(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", _TEST_DB)
    from app.models import FreezerItemCreate
    from app.services import inventory, inventory_pg

    calls = []
    real = inventory_pg._init_schema
    monkeypatch.setattr(inventory_pg, "_init_schema", lambda conn: (calls.append(1), real(conn)))
    inventory_pg._schema_ready.discard(_TEST_DB)

    inventory.clear("pool-test")
    inventory.create(FreezerItemCreate(species="elk", category="biggame", cut="ground", qty=1, unit="lbs",
                                       storage="vacuum_sealed", date_frozen=date.today()), "pool-test")
    for _ in range(3):
        assert len(inventory.list_items("pool-test")) == 1
    inventory.clear("pool-test")

    assert len(calls) == 1                     # DDL once, not per request
    pool = inventory_pg._pools[_TEST_DB]
    assert inventory_pg._pool() is pool       # same pool every time
    assert pool.get_stats()["pool_size"] <= 5
