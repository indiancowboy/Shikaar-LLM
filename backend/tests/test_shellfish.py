"""Shellfish category: parsing, shelf life, cut types, recipe matching, API."""
from __future__ import annotations

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app.domain import shelf_life, yield_profiles
from app.domain.cuts import cut_type_for
from app.domain.parsing import category_for, fallback_parse
from app.main import app
from app.models import FreezerItem
from app.services import inventory, recipes

client = TestClient(app)


def _item(species, cut) -> FreezerItem:
    return FreezerItem(id="itm_s", species=species, category="shellfish", cut=cut, qty=2,
                       unit="lbs", storage="vacuum_sealed",
                       date_frozen=date.today() - timedelta(days=10))


@pytest.mark.parametrize("name", ["dungeness crab", "crab", "shrimp", "prawns", "lobster",
                                  "crawfish", "scallops", "clams", "mussels", "oysters"])
def test_category_for_shellfish(name):
    assert category_for(name) == "shellfish"


def test_fallback_parses_crab_and_shrimp():
    res = fallback_parse("3 dungeness crabs, 1 lb crab meat and 2 lbs shrimp tails")
    by = {(c["species"], c["cut"]) for c in res}
    assert ("crab", "picked meat") in by
    assert ("shrimp", "tails") in by
    assert all(c["category"] == "shellfish" for c in res)


def test_shelf_life():
    assert shelf_life.shelf_life_months("shellfish", "vacuum_sealed") == 6
    assert shelf_life.shelf_life_months("shellfish", "wrapped") == 3


@pytest.mark.parametrize("species,cut,expected", [
    ("crab", "whole", "crab_whole"),
    ("dungeness_crab", "whole / mixed", "crab_whole"),
    ("crab", "clusters", "crab_whole"),
    ("crab", "legs", "crab_whole"),
    ("crab", "picked meat", "crab_meat"),
    ("crab", "lump meat", "crab_meat"),
    ("shrimp", "tails", None),
    ("lobster", "whole", None),
])
def test_cut_type_for_shellfish(species, cut, expected):
    assert cut_type_for("shellfish", cut, species) == expected


def test_whole_crab_matches_crab_recipes_only():
    fits = {m["recipe"]["id"]: m["kind"] for m in recipes.matches_for_item(_item("crab", "whole"))}
    assert fits == {
        "crab_pot_pie": "exact", "dungeness_crab_curry": "exact",
        "dungeness_crab_tikki": "exact", "nandu_rasam_with_crab_pakoras": "exact",
        "stuffed_crab_caranguejos_recheados": "exact",
    }


def test_picked_crab_meat_matches_tikki():
    fits = {m["recipe"]["id"] for m in recipes.matches_for_item(_item("crab", "picked meat"))}
    assert fits == {"dungeness_crab_tikki"}


def test_shrimp_has_no_library_recipes():
    assert recipes.matches_for_item(_item("shrimp", "tails")) == []


def test_api_accepts_shellfish():
    inventory.clear()
    r = client.post("/freezer", json={
        "species": "crab", "category": "shellfish", "cut": "whole", "qty": 3, "unit": "pkgs",
        "storage": "vacuum_sealed", "date_frozen": str(date.today()),
    })
    assert r.status_code == 201
    assert r.json()["shelf_life_months"] == 6
    inventory.clear()


def test_yield_estimate_for_crab():
    out = yield_profiles.estimate("dungeness crab", 4)
    assert out["category"] == "shellfish"
    assert out["candidates"][0]["cut"] == "picked meat" and out["edible_lbs"] == 1.0
