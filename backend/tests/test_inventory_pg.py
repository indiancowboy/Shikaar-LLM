"""Postgres store tests — exercised against a real Postgres.

Skipped unless SHIKAAR_TEST_DATABASE_URL points at a throwaway database. The
same logic the SQLite store is tested for (CRUD + per-owner isolation) is
verified here through the DATABASE_URL dispatch in `inventory`.
"""
from __future__ import annotations

import os
from datetime import date, timedelta

import pytest

_TEST_DB = os.environ.get("SHIKAAR_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not _TEST_DB, reason="set SHIKAAR_TEST_DATABASE_URL to run Postgres tests"
)


@pytest.fixture()
def inv(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", _TEST_DB)
    from app.services import inventory

    inventory.clear()  # whole table
    yield inventory
    inventory.clear()


def _data(**over):
    from app.models import FreezerItemCreate

    base = dict(
        species="whitetail", category="biggame", cut="backstrap", qty=2.0,
        unit="lbs", storage="vacuum_sealed",
        date_frozen=date.today() - timedelta(days=30),
    )
    base.update(over)
    return FreezerItemCreate(**base)


def test_pg_dispatch_active(inv):
    assert inv._use_pg() is True


def test_pg_crud_roundtrip(inv):
    item = inv.create(_data(), "user-a")
    assert item.id.startswith("itm_")

    listed = inv.list_items("user-a")
    assert len(listed) == 1 and listed[0].id == item.id
    assert listed[0].date_frozen == date.today() - timedelta(days=30)

    updated = inv.update(item.id, {"qty": 7.5}, "user-a")
    assert updated and updated.qty == 7.5
    assert inv.get(item.id, "user-a").qty == 7.5

    assert inv.delete(item.id, "user-a") is True
    assert inv.list_items("user-a") == []


def test_pg_owner_isolation(inv):
    a = inv.create(_data(), "user-a")
    inv.create(_data(species="elk", category="biggame"), "user-b")

    assert len(inv.list_items("user-a")) == 1
    assert len(inv.list_items("user-b")) == 1
    # user-b cannot see or mutate user-a's item
    assert inv.get(a.id, "user-b") is None
    assert inv.update(a.id, {"qty": 9}, "user-b") is None
    assert inv.delete(a.id, "user-b") is False
