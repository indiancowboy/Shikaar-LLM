"""Tests for the butchery yield engine."""
from __future__ import annotations

from app.domain.yield_profiles import estimate


def test_bear_300lb_estimate():
    out = estimate("black bear", 300)
    assert out["category"] == "bear"
    assert out["species"] == "black_bear"
    # ~0.35 * 300 = 105 lbs edible
    assert 95 <= out["edible_lbs"] <= 115
    # cut weights sum back to the edible total (within rounding)
    total = sum(c["qty"] for c in out["candidates"])
    assert abs(total - out["edible_lbs"]) <= 2.0
    assert all(c["category"] == "bear" for c in out["candidates"])


def test_dressed_weight_scales_up():
    live = estimate("whitetail", 150, dressed=False)["edible_lbs"]
    dressed = estimate("whitetail", 150, dressed=True)["edible_lbs"]
    assert dressed > live


def test_hog_keeps_compound_cut():
    out = estimate("wild hog", 200)
    cuts = {c["cut"] for c in out["candidates"]}
    assert "shoulder roast" in cuts


def test_unknown_species_defaults_to_biggame():
    out = estimate("jackalope", 80)
    assert out["category"] == "biggame"
