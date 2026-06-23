"""Tests for the deterministic fallback parser against the §14 fixtures."""
from __future__ import annotations

from app.domain.parsing import fallback_parse


def _by_species(res: list[dict]) -> dict[str, str]:
    return {c["species"]: c["category"] for c in res}


def test_fixture3_lean_vs_oily_fish_split():
    res = fallback_parse(
        "Got 4 redfish fillets and a couple pounds of catfish, plus three packs "
        "of salmon from the coast trip."
    )
    cats = _by_species(res)
    assert cats["salmon"] == "fishoily"
    assert cats["redfish"] == "fishlean"
    assert cats["catfish"] == "fishlean"


def test_fixture5_four_categories_in_one_sentence():
    res = fallback_parse(
        "Freezer dump: elk loin vac-sealed, two mallards, a dozen dove breasts, "
        "mackerel, snapper fillets, and about five pounds of wild boar sausage."
    )
    cats = _by_species(res)
    assert cats["mackerel"] == "fishoily"   # oily
    assert cats["snapper"] == "fishlean"    # lean
    assert cats["elk"] == "biggame"
    assert cats["wild_hog"] == "hog"
    assert cats["duck"] == "waterfowl"      # mallard -> duck
    assert cats["dove"] == "upland"


def test_fixture4_keeps_shoulder_roast_as_one_cut():
    res = fallback_parse(
        "Cleaned out a hog today — the rest got ground, some shoulder roasts, "
        "and a little bit of belly."
    )
    cuts = [c["cut"] for c in res]
    assert "shoulder roast" in cuts
    assert "shoulder" not in cuts  # not split into shoulder + roast
    assert "ground" in cuts and "belly" in cuts


def test_never_silently_drops_a_named_species():
    res = fallback_parse("two mallards and a goose, all wrapped")
    species = {c["species"] for c in res}
    assert "duck" in species and "goose" in species
    # no cut named -> logged whole, never dropped
    assert all(c["cut"] in ("whole / mixed",) for c in res)
    assert all(c["storage"] == "wrapped" for c in res)


def test_no_species_returns_empty():
    assert fallback_parse("put some random stuff in the freezer") == []
