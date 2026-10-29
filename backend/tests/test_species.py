"""Species catalog: integrity, lookups, parser wiring, new categories, endpoint."""
from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app.domain import shelf_life, species
from app.domain.cuts import RECIPE_CATEGORIES
from app.domain.parsing import category_for, fallback_parse
from app.main import app
from app.models import FreezerItem
from app.services import freezer_parse, recipes

client = TestClient(app)


# ----------------------------------------------------------- integrity --------
def test_catalog_integrity():
    cat = species.catalog()
    assert len(cat) >= 150
    keys = [s.key for s in cat]
    assert len(keys) == len(set(keys)), "duplicate species keys"
    owners = defaultdict(set)
    for s in cat:
        assert s.category in species.CATEGORIES
        assert s.category in RECIPE_CATEGORIES
        for a in s.aliases:
            owners[a].add(s.key)
    assert not {a: k for a, k in owners.items() if len(k) > 1}, "alias used by two species"


def test_existing_keys_unchanged():
    """Items already in freezers use these keys — they must keep resolving."""
    for key in ("whitetail", "mule_deer", "elk", "nilgai", "antelope", "black_bear", "wild_hog",
                "duck", "teal", "goose", "dove", "quail", "pheasant", "turkey", "redfish",
                "catfish", "walleye", "snapper", "bass", "salmon", "mackerel", "tuna",
                "crab", "shrimp", "lobster", "crawfish", "scallops", "clams", "mussels", "oysters"):
        assert species.by_key(key) is not None, key


# -------------------------------------------------------------- lookups -------
@pytest.mark.parametrize("text,key,category", [
    ("elk", "elk", "biggame"),
    ("bull elk", "elk", "biggame"),
    ("moose", "moose", "biggame"),
    ("caribou", "caribou", "biggame"),
    ("aoudad", "aoudad", "biggame"),
    ("mountain goat", "mountain_goat", "biggame"),
    ("goat", "goat", "redmeat"),
    ("lamb", "lamb", "redmeat"),
    ("ground beef", "beef", "redmeat"),
    ("chicken", "chicken", "poultry"),
    ("prairie chicken", "prairie_chicken", "upland"),
    ("rabbit", "rabbit", "smallgame"),
    ("snow geese", "snow_goose", "waterfowl"),
    ("ruffed grouse", "ruffed_grouse", "upland"),
    ("walleye", "walleye", "fishlean"),
    ("halibut", "halibut", "fishlean"),
    ("king salmon", "salmon", "fishoily"),
    ("speckled trout", "seatrout", "fishlean"),
    ("lake trout", "lake_trout", "fishoily"),
    ("javelina", "javelina", "hog"),
    ("pork", "pork", "hog"),
    ("grizzly", "brown_bear", "bear"),
    ("black cod", "sablefish", "fishoily"),
    ("codfish", "cod", "fishlean"),
    ("king crab", "king_crab", "shellfish"),
])
def test_lookup(text, key, category):
    s = species.lookup(text)
    assert s is not None and (s.key, s.category) == (key, category)


@pytest.mark.parametrize("text", ["program", "char the skin", "a sprig of rosemary", "alligator", ""])
def test_no_false_matches(text):
    assert species.lookup(text) is None


# ---------------------------------------------------------------- parser ------
def test_fallback_parse_uses_catalog():
    res = fallback_parse("2 snow geese, a bull elk backstrap and 10 2 lb packs of ground goat")
    got = {(c["species"], c["category"]) for c in res}
    assert ("snow_goose", "waterfowl") in got
    assert ("elk", "biggame") in got
    assert ("goat", "redmeat") in got
    goat = next(c for c in res if c["species"] == "goat")
    assert goat["cut"] == "ground" and goat["packs"] == 10


def test_category_for_compat():
    assert category_for("wild boar") == "hog"
    assert category_for("whitetail") == "biggame"
    assert category_for("kraken") is None


def test_coerce_snaps_model_species_to_catalog_key():
    [c] = freezer_parse.coerce_all(
        [{"species": "Wild Boar", "category": "hog", "cut": "ground", "qty": 2, "unit": "lbs"}],
        offline=False)
    assert c.species == "wild_hog"
    [c] = freezer_parse.coerce_all(
        [{"species": "bull moose", "category": "not-a-category", "cut": "roast", "qty": 3, "unit": "lbs"}],
        offline=False)
    assert (c.species, c.category) == ("moose", "biggame")
    [c] = freezer_parse.coerce_all(
        [{"species": "alligator", "category": "fishlean", "cut": "tail", "qty": 2, "unit": "lbs"}],
        offline=False)
    assert (c.species, c.category) == ("alligator", "fishlean")  # unknown species kept as given


def test_prompt_lists_new_categories_and_species():
    t = freezer_parse.EXTRACTION_INSTRUCTIONS
    for word in ("redmeat", "poultry", "smallgame", "moose", "chicken", "goat", "__"):
        if word == "__":
            assert "__" not in t  # placeholders all filled
        else:
            assert word in t


# ---------------------------------------------------------- new categories ----
def test_new_category_shelf_life():
    assert shelf_life.shelf_life_months("poultry", "vacuum_sealed") == 12
    assert shelf_life.shelf_life_months("redmeat", "wrapped") == 6
    assert shelf_life.shelf_life_months("smallgame", "vacuum_sealed") == 9


def _item(sp, category, cut) -> FreezerItem:
    return FreezerItem(id="itm_x", species=sp, category=category, cut=cut, qty=2, unit="lbs",
                       storage="vacuum_sealed", date_frozen=date.today() - timedelta(days=5))


def test_ground_goat_matches_keema_recipes():
    fits = {m["recipe"]["id"] for m in recipes.matches_for_item(_item("goat", "redmeat", "ground"))}
    assert {"keema_ground_meat", "butter_keema", "keema_kachori"} <= fits


def test_chicken_matches_no_library_recipe():
    assert recipes.matches_for_item(_item("chicken", "poultry", "breasts")) == []


@pytest.mark.parametrize("category", ["poultry", "redmeat", "smallgame"])
def test_api_accepts_new_categories(category):
    r = client.post("/freezer", json={
        "species": "test", "category": category, "cut": "whole", "qty": 1, "unit": "lbs",
        "storage": "vacuum_sealed", "date_frozen": str(date.today()),
    })
    assert r.status_code == 201
    client.delete(f"/freezer/{r.json()['id']}")


# -------------------------------------------------------------- endpoint ------
def test_species_endpoint():
    body = client.get("/species").json()
    keys = {s["key"] for s in body["species"]}
    assert {"elk", "moose", "chicken", "goat"} <= keys
    assert {c["key"] for c in body["categories"]} == set(species.CATEGORIES)
    elk = next(s for s in body["species"] if s["key"] == "elk")
    assert elk["category"] == "biggame" and "wapiti" in elk["aliases"]


def test_groups_cover_catalog_and_domestic_holds_farm_meats():
    assert {s.group for s in species.catalog()} == set(species.GROUPS)
    assert species.GROUPS[-1] == "Domestic"
    domestic = {s.key for s in species.catalog() if s.group == "Domestic"}
    assert {"chicken", "beef", "lamb", "goat", "pork", "pekin_duck"} <= domestic
    # group is display-only: pork still keeps like hog
    assert species.by_key("pork").category == "hog"
    assert species.lookup("pork").key == "pork" and species.lookup("wild boar").key == "wild_hog"


def test_species_endpoint_lists_groups_in_order():
    assert client.get("/species").json()["groups"] == list(species.GROUPS)
