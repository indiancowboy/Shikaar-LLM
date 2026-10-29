"""Recipe catalog + cut-aware matching (offline)."""
from __future__ import annotations

import json
from datetime import date, timedelta

import pytest

import build_recipe_catalog
from app.domain.cuts import cut_type_for, match_kind
from app.models import FreezerItem
from app.services import recipes


def _item(species, category, cut, **over) -> FreezerItem:
    base = dict(id="itm_x", species=species, category=category, cut=cut, qty=2, unit="lbs",
                storage="vacuum_sealed", date_frozen=date.today() - timedelta(days=10))
    base.update(over)
    return FreezerItem(**base)


def _titles(item) -> dict[str, str]:
    return {m["recipe"]["id"]: m["kind"] for m in recipes.matches_for_item(item)}


# ------------------------------------------------------------- catalog --------
def test_catalog_in_sync_with_knowledge_base():
    """Fails when a recipe .md was edited without re-running build_recipe_catalog.py."""
    on_disk = json.loads(build_recipe_catalog.OUT.read_text(encoding="utf-8"))
    assert on_disk == build_recipe_catalog.build()


def test_every_recipe_tagged():
    cat = recipes.catalog()
    assert len(cat) == 25
    assert all(r["categories"] and r["cuts"] and r["text"] for r in cat.values())


# ---------------------------------------------------------- cut types ---------
@pytest.mark.parametrize("category,cut,expected", [
    ("hog", "ground", "ground"),
    ("hog", "breakfast sausage", "sausage"),
    ("biggame", "backstrap", "tender"),
    ("biggame", "shoulder roast", "braise"),
    ("biggame", "steaks", "tender"),
    ("waterfowl", "breasts", "breast"),
    ("upland", "whole", "whole_bird"),
    ("fishlean", "fillets", "fillet"),
    ("fishoily", "loin", "fillet"),
    ("fishlean", "whole / mixed", "fillet"),
    ("biggame", "whole / mixed", None),
])
def test_cut_type_for(category, cut, expected):
    assert cut_type_for(category, cut) == expected


def test_match_kind():
    assert match_kind("ground", ["ground"]) == ("exact", None)
    kind, note = match_kind("ground", ["sausage"])
    assert kind == "adapt" and "sausage" in note.lower()
    assert match_kind("tender", ["ground"]) == (None, None)
    assert match_kind(None, ["ground"]) == (None, None)


# ------------------------------------------------------------ matching --------
def test_ground_boar_gets_ground_recipes_and_adapted_sausage_pizza():
    fits = _titles(_item("wild_hog", "hog", "ground"))
    for rid in ("butter_keema", "keema_ground_meat", "keema_kachori", "desi_deer_flatbread", "wild_boar_mirchi_bajji"):
        assert fits[rid] == "exact"
    assert fits["wild_boar_breakfast_pizza"] == "adapt"
    # never steak/tenderloin or fish recipes for ground meat
    assert "cambodianstyle_deer_tenderloin" not in fits and "venison_curry" not in fits
    assert not any("fish" in rid or "crab" in rid for rid in fits)
    # exact fits listed before adapted ones
    kinds = [m["kind"] for m in recipes.matches_for_item(_item("wild_hog", "hog", "ground"))]
    assert kinds == sorted(kinds, key=lambda k: k != "exact")


def test_low_temp_sous_vide_recipes_are_deer_only():
    assert set(_titles(_item("whitetail", "biggame", "backstrap"))) == {"cambodianstyle_deer_tenderloin", "venison_curry"}
    assert _titles(_item("wild_hog", "hog", "tenderloin")) == {}
    assert _titles(_item("black_bear", "bear", "backstrap")) == {}


def test_fish_split_lean_vs_oily():
    lean = _titles(_item("redfish", "fishlean", "fillets"))
    oily = _titles(_item("tuna", "fishoily", "loin"))
    assert "berbere_spiced_rockfish" in lean and "berbere_spiced_rockfish" not in oily
    assert "bluefin_tuna_butter_masala" in oily and "bluefin_tuna_butter_masala" not in lean
    assert "kasundi_fish_tikka" in lean and "kasundi_fish_tikka" in oily


def test_birds():
    assert set(_titles(_item("goose", "waterfowl", "breasts"))) == {"ponzu_ginger_goose"}
    assert _titles(_item("duck", "waterfowl", "whole")) == {"ponzu_ginger_goose": "adapt"}
    assert _titles(_item("duck", "waterfowl", "legs")) == {}


def test_candidates_groups_fits_by_recipe():
    ground = _item("wild_hog", "hog", "ground", id="itm_g")
    venison = _item("whitetail", "biggame", "ground", id="itm_v")
    c = recipes.candidates([ground, venison])
    assert [f["item_id"] for f in c["butter_keema"]["fits"]] == ["itm_g", "itm_v"]
