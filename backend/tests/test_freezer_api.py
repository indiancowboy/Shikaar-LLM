"""Integration tests for the Freezer endpoints (offline — model call patched)."""
from __future__ import annotations

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

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
        species="whitetail", category="biggame", cut="backstrap", qty=2,
        unit="lbs", storage="vacuum_sealed",
        date_frozen=str(date.today() - timedelta(days=30)),
    )
    base.update(over)
    return base


def test_crud_roundtrip():
    r = client.post("/freezer", json=_item())
    assert r.status_code == 201
    body = r.json()
    iid = body["id"]
    assert body["status"] in ("prime", "good", "use_soon", "past_prime")
    assert body["age_months"] >= 0.9

    assert client.get("/freezer").json()[0]["id"] == iid

    r2 = client.patch(f"/freezer/{iid}", json={"qty": 5})
    assert r2.status_code == 200 and r2.json()["qty"] == 5

    assert client.delete(f"/freezer/{iid}").status_code == 204
    assert client.get("/freezer").json() == []


def test_validation_rejects_bad_input():
    assert client.post("/freezer", json=_item(qty=0)).status_code == 422
    assert client.post("/freezer", json=_item(category="dragon")).status_code == 422
    future = str(date.today() + timedelta(days=5))
    assert client.post("/freezer", json=_item(date_frozen=future)).status_code == 422


def test_patch_missing_item_404():
    assert client.patch("/freezer/itm_nope", json={"qty": 1}).status_code == 404


def test_estimate_yield_endpoint():
    r = client.post("/freezer/estimate-yield", json={"species": "black bear", "weight": 300})
    assert r.status_code == 200
    d = r.json()
    assert d["category"] == "bear"
    assert d["candidates"]
    assert d["edible_lbs"] > 0


def test_parse_falls_back_when_model_unreachable(monkeypatch):
    def boom(text):
        raise RuntimeError("model down")

    monkeypatch.setattr(freezer_parse, "_llm_extract", boom)
    r = client.post("/freezer/parse", json={"text": "two deer backstraps and 8 lbs ground"})
    assert r.status_code == 200
    d = r.json()
    assert d["parsed_offline"] is True
    assert any(c["species"] == "whitetail" for c in d["candidates"])


def test_cook_first_empty_is_calm():
    r = client.get("/freezer/cook-first")
    assert r.status_code == 200
    assert r.json() == {"urgent": False, "cards": []}


def test_meal_plan_empty_no_model_call():
    r = client.post("/freezer/meal-plan", json={})
    assert r.status_code == 200
    assert "Nothing in the freezer" in r.json()["plan"]
