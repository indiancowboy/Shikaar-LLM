"""Unit tests for the species-aware shelf-life math (brief §4, §13)."""
from __future__ import annotations

from datetime import date, timedelta

import pytest

from app.domain import shelf_life as sl


def _frozen_months_ago(months: float) -> date:
    return date.today() - timedelta(days=months * sl.DAYS_PER_MONTH)


@pytest.mark.parametrize(
    "category,storage,expected",
    [
        ("biggame", "vacuum_sealed", 24),
        ("biggame", "wrapped", 9),
        ("hog", "vacuum_sealed", 6),
        ("bear", "vacuum_sealed", 6),  # bear defaults to hog profile
        ("fishlean", "wrapped", 3),
        ("fishoily", "vacuum_sealed", 3),
        ("fishoily", "wrapped", 2),
    ],
)
def test_shelf_life_lookup(category, storage, expected):
    assert sl.shelf_life_months(category, storage) == expected


def test_unknown_combo_uses_default():
    assert sl.shelf_life_months("dragon", "vacuum_sealed") == sl.DEFAULT_SHELF_LIFE_MONTHS


@pytest.mark.parametrize(
    "pct_of_life,expected_status",
    [
        (0.10, "prime"),
        (0.49, "prime"),
        (0.60, "good"),
        (0.84, "good"),
        (0.90, "use_soon"),
        (0.99, "use_soon"),
        # exactly 1.00 is unreachable here: timedelta.days truncates fractional
        # days, so we test just past the boundary instead.
        (1.05, "past_prime"),
        (1.50, "past_prime"),
    ],
)
def test_status_thresholds(pct_of_life, expected_status):
    # biggame/vacuum_sealed = 24 mo; freeze it pct_of_life * 24 months ago.
    life = 24
    frozen = _frozen_months_ago(pct_of_life * life)
    out = sl.freshness("biggame", "vacuum_sealed", frozen)
    assert out["status"] == expected_status


def test_lean_vs_oily_fish_diverge():
    # Same age, same storage: oily fish degrades faster than lean.
    frozen = _frozen_months_ago(4)
    lean = sl.freshness("fishlean", "vacuum_sealed", frozen)  # 6-mo life
    oily = sl.freshness("fishoily", "vacuum_sealed", frozen)  # 3-mo life
    assert lean["status"] in ("prime", "good")
    assert oily["status"] == "past_prime"


def test_age_months_and_pct_capped():
    frozen = _frozen_months_ago(48)  # way past a 24-mo life
    out = sl.freshness("biggame", "vacuum_sealed", frozen)
    assert out["age_months"] == pytest.approx(48, abs=0.5)
    assert out["pct"] <= 1.08  # gauge cap
    assert out["status"] == "past_prime"
