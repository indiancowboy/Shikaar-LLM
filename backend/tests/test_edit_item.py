"""Editing items already in the freezer (PATCH /freezer/{id})."""
from __future__ import annotations

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import inventory

client = TestClient(app)
ME = {"X-Client-Id": "editor"}


@pytest.fixture(autouse=True)
def _clean():
    inventory.clear()
    yield
    inventory.clear()


def _add(**over) -> str:
    body = dict(species="mule_deer", category="biggame", cut="unknown", qty=12, unit="pkgs",
                storage="vacuum_sealed", date_frozen=str(date.today()))
    body.update(over)
    r = client.post("/freezer", json=body, headers=ME)
    assert r.status_code == 201
    return r.json()["id"]


def test_fix_species_cut_and_count():
    iid = _add()
    r = client.patch(f"/freezer/{iid}", json={"species": "elk", "category": "biggame", "cut": "backstrap", "qty": 2},
                     headers=ME)
    assert r.status_code == 200
    d = r.json()
    assert (d["species"], d["cut"], d["qty"], d["unit"]) == ("elk", "backstrap", 2, "pkgs")


def test_set_packs_on_plain_item_recomputes_total():
    iid = _add(cut="ground", qty=8, unit="lbs")
    d = client.patch(f"/freezer/{iid}", json={"packs": 4, "pack_size": 2}, headers=ME).json()
    assert (d["packs"], d["pack_size"], d["qty"]) == (4, 2, 8)


def test_clear_packs_back_to_plain_count():
    iid = _add(cut="ground", qty=10, unit="lbs", packs=10, pack_size=1)
    d = client.patch(f"/freezer/{iid}", json={"packs": None, "pack_size": None, "unit": "pkgs", "qty": 3},
                     headers=ME).json()
    assert (d["packs"], d["pack_size"], d["qty"], d["unit"]) == (None, None, 3, "pkgs")


def test_change_date_and_storage_updates_shelf_life():
    iid = _add(category="hog", species="wild_hog")
    old = str(date.today() - timedelta(days=200))
    d = client.patch(f"/freezer/{iid}", json={"date_frozen": old, "storage": "wrapped"}, headers=ME).json()
    assert d["date_frozen"] == old and d["storage"] == "wrapped"
    assert d["status"] == "past_prime"  # wrapped hog keeps ~4 months


def test_future_date_rejected():
    iid = _add()
    future = str(date.today() + timedelta(days=3))
    assert client.patch(f"/freezer/{iid}", json={"date_frozen": future}, headers=ME).status_code == 422


def test_cannot_edit_someone_elses_item():
    iid = _add()
    r = client.patch(f"/freezer/{iid}", json={"cut": "roast"}, headers={"X-Client-Id": "someone-else"})
    assert r.status_code == 404
