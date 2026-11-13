"""Clear freezer: empties only the caller's own items."""
from __future__ import annotations

from datetime import date

from fastapi.testclient import TestClient

from app.main import app
from app.services import inventory

client = TestClient(app)


def _add(client_id: str, cut: str):
    r = client.post("/freezer", json={
        "species": "elk", "category": "biggame", "cut": cut, "qty": 2, "unit": "lbs",
        "storage": "vacuum_sealed", "date_frozen": str(date.today()),
    }, headers={"X-Client-Id": client_id})
    assert r.status_code == 201


def test_clear_removes_only_my_items():
    inventory.clear()
    for cut in ("ground", "steaks", "roast"):
        _add("alice", cut)
    _add("bob", "ground")

    r = client.delete("/freezer", headers={"X-Client-Id": "alice"})
    assert r.status_code == 200 and r.json() == {"removed": 3}
    assert client.get("/freezer", headers={"X-Client-Id": "alice"}).json() == []
    assert len(client.get("/freezer", headers={"X-Client-Id": "bob"}).json()) == 1
    inventory.clear()


def test_clear_empty_freezer_is_fine():
    inventory.clear()
    assert client.delete("/freezer", headers={"X-Client-Id": "nobody"}).json() == {"removed": 0}
