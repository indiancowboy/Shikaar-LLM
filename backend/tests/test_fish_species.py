"""Tests for the FishBase-derived fish-species reference (offline)."""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.services import fish_species

client = TestClient(app)


def test_lookup_by_alias_and_scientific_name():
    assert fish_species.lookup("redfish")["scientific_name"] == "Sciaenops ocellatus"
    assert fish_species.lookup("red drum")["key"] == "redfish"
    assert fish_species.lookup("Sciaenops ocellatus")["key"] == "redfish"
    assert fish_species.lookup("ahi")["key"] == "yellowfin_tuna"


def test_lean_oily_classification_matches_shelf_life_categories():
    assert fish_species.category_for("salmon") == "fishoily"
    assert fish_species.category_for("mackerel") == "fishoily"
    assert fish_species.category_for("redfish") == "fishlean"
    assert fish_species.category_for("snapper") == "fishlean"


def test_unknown_species_returns_none():
    assert fish_species.lookup("kraken") is None
    assert fish_species.category_for("kraken") is None


def test_fish_endpoints():
    listing = client.get("/fish").json()
    assert len(listing["species"]) >= 10

    r = client.get("/fish/lingcod")
    assert r.status_code == 200
    assert r.json()["scientific_name"] == "Ophiodon elongatus"

    assert client.get("/fish/kraken").status_code == 404
