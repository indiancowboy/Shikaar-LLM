"""Species-aware shelf-life model (build brief §4) — the core differentiator.

Shelf life depends on fat content, encoded via `category` + `storage`. Kept as
data + pure functions so business logic never hardcodes the numbers and the
math is trivially testable. Status (`status`, `age_months`) is always derived
here, server-side — never trusted from a client.
"""
from __future__ import annotations

from datetime import date

# Months of freezer life by category + storage method (brief §4).
# NOTE: `bear` is not in the brief's original enum. Bears are fatty, so we
# default their profile to match `hog` (short life). Flagged as a reversible
# decision — tune independently here if real-world numbers differ.
SHELF_LIFE_MONTHS: dict[str, dict[str, int]] = {
    "biggame":   {"vacuum_sealed": 24, "wrapped": 9},   # venison, elk, nilgai, antelope (lean)
    "hog":       {"vacuum_sealed": 6,  "wrapped": 4},   # wild hog/boar (fatty)
    "bear":      {"vacuum_sealed": 6,  "wrapped": 4},   # fatty — defaults to hog profile
    "waterfowl": {"vacuum_sealed": 6,  "wrapped": 4},   # duck, goose, teal (fatty)
    "upland":    {"vacuum_sealed": 9,  "wrapped": 6},   # dove, quail, pheasant, turkey
    "fishlean":  {"vacuum_sealed": 6,  "wrapped": 3},   # redfish, catfish, bass, walleye, snapper
    "fishoily":  {"vacuum_sealed": 3,  "wrapped": 2},   # salmon, mackerel, tuna (degrade fast)
}

DEFAULT_SHELF_LIFE_MONTHS = 9  # fallback when a combo is missing (brief §4)
DAYS_PER_MONTH = 30.44

# Status thresholds on the age/shelf_life ratio (brief §4). Checked in order;
# first threshold the ratio falls under wins. Anything >= 1.0 is past prime.
STATUS_THRESHOLDS: tuple[tuple[float, str], ...] = (
    (0.50, "prime"),
    (0.85, "good"),
    (1.00, "use_soon"),
)
PAST_PRIME = "past_prime"


def age_months(date_frozen: date, *, today: date | None = None) -> float:
    """Age in months since `date_frozen` (brief §4: days / 30.44)."""
    today = today or date.today()
    return (today - date_frozen).days / DAYS_PER_MONTH


def shelf_life_months(category: str, storage: str) -> int:
    """Look up shelf life for a category/storage combo, with the §4 default."""
    return SHELF_LIFE_MONTHS.get(category, {}).get(storage, DEFAULT_SHELF_LIFE_MONTHS)


def freshness(
    category: str,
    storage: str,
    date_frozen: date,
    *,
    today: date | None = None,
) -> dict:
    """Compute freshness for an item.

    Returns a dict with:
      - status: one of prime | good | use_soon | past_prime
      - age_months: rounded age
      - pct: age / shelf_life (capped at 1.08 for gauge display, matching the
        prototype so the cold-life bar can overflow slightly past "spent")
      - shelf_life_months: the looked-up life
    """
    life = shelf_life_months(category, storage)
    age = age_months(date_frozen, today=today)
    pct = age / life if life else 1.0

    status = PAST_PRIME
    for threshold, label in STATUS_THRESHOLDS:
        if pct < threshold:
            status = label
            break

    return {
        "status": status,
        "age_months": round(age, 1),
        "pct": min(pct, 1.08),
        "shelf_life_months": life,
    }
