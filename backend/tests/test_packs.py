"""Uniform packs: derived totals, the "used one" endpoint, and pack parsing."""
from __future__ import annotations

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app.domain.parsing import fallback_parse
from app.main import app
from app.services import freezer_parse, inventory

client = TestClient(app)


@pytest.fixture(autouse=True)
def _clear_store():
    inventory.clear()
    yield
    inventory.clear()


def _item(**over) -> dict:
    base = dict(
        species="wild_hog", category="hog", cut="ground", qty=1, unit="lbs",
        storage="vacuum_sealed", date_frozen=str(date.today() - timedelta(days=5)),
    )
    base.update(over)
    return base


# ------------------------------------------------------------------ model -----
def test_packs_derive_total_weight():
    r = client.post("/freezer", json=_item(packs=10, pack_size=2, qty=999))
    assert r.status_code == 201
    body = r.json()
    assert body["packs"] == 10 and body["pack_size"] == 2
    assert body["qty"] == 20  # derived, client's qty ignored


def test_packs_validation():
    assert client.post("/freezer", json=_item(packs=10)).status_code == 422  # no size
    assert client.post("/freezer", json=_item(pack_size=2)).status_code == 422  # no count
    assert client.post("/freezer", json=_item(packs=2, pack_size=1, unit="pkgs")).status_code == 422
    assert client.post("/freezer", json=_item(packs=0, pack_size=2)).status_code == 422


def test_plain_items_unchanged():
    body = client.post("/freezer", json=_item(qty=8)).json()
    assert body["qty"] == 8 and body["packs"] is None and body["pack_size"] is None


# ------------------------------------------------------------- used one -------
def test_use_decrements_packs_then_removes():
    iid = client.post("/freezer", json=_item(packs=2, pack_size=2)).json()["id"]

    r = client.post(f"/freezer/{iid}/use")
    assert r.status_code == 200
    assert r.json()["removed"] is False
    assert r.json()["item"]["packs"] == 1 and r.json()["item"]["qty"] == 2

    r = client.post(f"/freezer/{iid}/use")
    assert r.json() == {"removed": True, "item": None}
    assert client.get("/freezer").json() == []


def test_use_count_and_pkgs_unit():
    iid = client.post("/freezer", json=_item(cut="backstrap", qty=3, unit="pkgs")).json()["id"]
    r = client.post(f"/freezer/{iid}/use", json={"count": 2})
    assert r.json()["item"]["qty"] == 1
    assert client.post(f"/freezer/{iid}/use").json()["removed"] is True


def test_use_bulk_weight_item_removes_it():
    iid = client.post("/freezer", json=_item(qty=8)).json()["id"]
    assert client.post(f"/freezer/{iid}/use").json()["removed"] is True


def test_use_missing_or_foreign_item_404():
    assert client.post("/freezer/itm_nope/use").status_code == 404
    iid = client.post(
        "/freezer", json=_item(packs=3, pack_size=1), headers={"X-Client-Id": "alice"}
    ).json()["id"]
    assert client.post(f"/freezer/{iid}/use", headers={"X-Client-Id": "bob"}).status_code == 404


# --------------------------------------------------------------- parsing ------
@pytest.mark.parametrize(
    "text",
    [
        "10 2 pound packs of ground wild boar",
        "10 packs of 2 lb ground wild boar",
        "wild boar: 10 x 2lb packs ground",
    ],
)
def test_fallback_parses_uniform_packs(text):
    res = fallback_parse(text)
    ground = [c for c in res if c["cut"] == "ground"]
    assert len(ground) == 1
    c = ground[0]
    assert c["species"] == "wild_hog"
    assert c["packs"] == 10 and c["pack_size"] == 2.0 and c["qty"] == 20.0
    assert c["unit"] == "lbs"


def test_fallback_without_packs_unchanged():
    c = [c for c in fallback_parse("venison, about 8 lbs ground") if c["cut"] == "ground"][0]
    assert c["qty"] == 8.0 and "packs" not in c


def test_coerce_recomputes_total_from_packs():
    [c] = freezer_parse.coerce_all(
        [{"species": "wild_hog", "category": "hog", "cut": "ground", "qty": 21,
          "unit": "lbs", "storage": "vacuum_sealed", "packs": 10, "pack_size": 2}],
        offline=False,
    )
    assert c.packs == 10 and c.pack_size == 2 and c.qty == 20


def test_coerce_count_without_weight_becomes_pkgs():
    [c] = freezer_parse.coerce_all(
        [{"species": "whitetail", "category": "biggame", "cut": "backstrap",
          "qty": 2, "unit": "pkgs", "packs": 2, "pack_size": None}],
        offline=False,
    )
    assert c.unit == "pkgs" and c.qty == 2 and c.packs is None and c.pack_size is None


def test_parse_endpoint_returns_packs(monkeypatch):
    monkeypatch.setattr(
        freezer_parse, "_llm_extract",
        lambda text: [{"species": "wild boar", "category": "hog", "cut": "ground",
                       "qty": 20, "unit": "lbs", "packs": 10, "pack_size": 2}],
    )
    d = client.post("/freezer/parse", json={"text": "10 2 pound packs of ground wild boar"}).json()
    assert d["candidates"][0]["packs"] == 10 and d["candidates"][0]["qty"] == 20
