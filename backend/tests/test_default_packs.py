"""Ground meat and sausage default to 1 lb packs when no packs are given."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.domain.cuts import default_packs
from app.main import app
from app.services import freezer_parse

client = TestClient(app)


def _coerce(**entry):
    base = {"species": "wild_hog", "category": "hog", "cut": "ground", "qty": 15, "unit": "lbs"}
    base.update(entry)
    [c] = freezer_parse.coerce_all([base], offline=False)
    return c


@pytest.mark.parametrize("cut,qty,packs", [
    ("ground", 15, 15),
    ("breakfast sausage", 6, 6),
    ("ground", 15.4, 15),
    ("ground", 0.4, 1),
])
def test_bare_weight_becomes_one_pound_packs(cut, qty, packs):
    c = _coerce(cut=cut, qty=qty)
    assert (c.packs, c.pack_size, c.qty) == (packs, 1.0, float(packs))


def test_explicit_packs_are_kept():
    c = _coerce(qty=16, packs=8, pack_size=2)
    assert (c.packs, c.pack_size, c.qty) == (8, 2.0, 16.0)


@pytest.mark.parametrize("entry", [
    {"unit": "kg", "qty": 5},                                  # not lbs
    {"unit": "pkgs", "qty": 3},                                # count, no weight
    {"cut": "backstrap", "qty": 4},                            # not ground
    {"species": "whitetail", "category": "biggame", "cut": "steaks", "qty": 6},
    {"species": "redfish", "category": "fishlean", "cut": "fillets", "qty": 5},
])
def test_other_items_untouched(entry):
    c = _coerce(**entry)
    assert c.packs is None and c.pack_size is None


def test_default_packs_direct():
    assert default_packs("biggame", "ground", "whitetail", 8.0, "lbs", None, None) == (8.0, 8, 1.0)
    assert default_packs("biggame", "roast", "whitetail", 8.0, "lbs", None, None) == (8.0, None, None)


def test_offline_fallback_packs_ground(monkeypatch):
    def boom(text):
        raise RuntimeError("model down")
    monkeypatch.setattr(freezer_parse, "_llm_extract", boom)
    d = client.post("/freezer/parse", json={"text": "venison, about 8 lbs ground and two backstraps"}).json()
    ground = next(c for c in d["candidates"] if c["cut"] == "ground")
    assert (ground["packs"], ground["pack_size"], ground["qty"]) == (8, 1.0, 8.0)
    backstrap = next(c for c in d["candidates"] if c["cut"] == "backstrap")
    assert backstrap["packs"] is None


def test_yield_estimate_packs_ground():
    d = client.post("/freezer/estimate-yield", json={"species": "black bear", "weight": 300}).json()
    ground = next(c for c in d["candidates"] if c["cut"] == "ground")
    assert ground["pack_size"] == 1.0 and ground["packs"] == ground["qty"] == round(ground["qty"])
    roasts = next(c for c in d["candidates"] if c["cut"] == "roasts")
    assert roasts["packs"] is None
