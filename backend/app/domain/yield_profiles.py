"""Butchery yield engine (added 2026-06) — "I butchered a 300 lb bear".

Structured config + math (NOT vector-RAG): live/dressed weight -> edible boneless
meat -> a cut breakdown -> candidate freezer entries that flow into the SAME
human-confirm step as the text/image parser. Numbers are estimates and swing
widely (a fall bear is far fatter than a spring one), so every output is meant
to be reviewed and edited before committing. Tune the table here, not in logic.
"""
from __future__ import annotations

from . import parsing

# live weight -> field-dressed weight (big-game approximation).
FIELD_DRESS_FRACTION = 0.78

# category -> (edible boneless fraction of LIVE weight, {cut: relative share}).
# Cut shares need not sum to 1.0 exactly — they're normalized at compute time.
YIELD_PROFILES: dict[str, tuple[float, dict[str, float]]] = {
    "biggame": (0.42, {
        "backstrap": 0.09, "tenderloin": 0.03, "hindquarter roasts": 0.22,
        "steaks": 0.14, "shoulder roast": 0.12, "ground": 0.36, "ribs": 0.04,
    }),
    "bear": (0.35, {
        "backstrap": 0.08, "roasts": 0.40, "steaks": 0.10, "ground": 0.40, "ribs": 0.02,
    }),
    "hog": (0.38, {
        "shoulder roast": 0.24, "ham roast": 0.20, "loin": 0.12, "belly": 0.10,
        "ground": 0.29, "ribs": 0.05,
    }),
    "waterfowl": (0.45, {"breasts": 0.55, "legs": 0.20, "whole / mixed": 0.25}),
    "upland": (0.45, {"breasts": 0.60, "legs": 0.25, "whole / mixed": 0.15}),
    "fishlean": (0.45, {"fillets": 1.0}),
    "fishoily": (0.50, {"fillets": 1.0}),
}

DEFAULT_CATEGORY = "biggame"


def estimate(species: str, weight: float, dressed: bool = False) -> dict:
    """Estimate freezer entries from an animal's weight.

    Args:
        species: e.g. "black bear", "whitetail", "wild hog".
        weight: pounds. Treated as LIVE weight unless `dressed=True`.
        dressed: True if `weight` is field-dressed rather than live.

    Returns a dict:
        {
          "species": normalized species,
          "category": resolved category,
          "edible_lbs": total estimated boneless meat,
          "candidates": [ {species, category, cut, qty, unit, storage}, ... ],
        }
    """
    category = parsing.category_for(species) or DEFAULT_CATEGORY
    edible_fraction, cuts = YIELD_PROFILES.get(category, YIELD_PROFILES[DEFAULT_CATEGORY])

    # When the user gives a dressed weight, scale the live-based fraction up.
    fraction = edible_fraction / FIELD_DRESS_FRACTION if dressed else edible_fraction
    edible_lbs = weight * fraction

    total_share = sum(cuts.values()) or 1.0
    norm_species = species.lower().strip().replace(" ", "_")

    candidates: list[dict] = []
    for cut, share in cuts.items():
        lbs = round(edible_lbs * share / total_share, 1)
        if lbs < 0.1:
            continue
        candidates.append({
            "species": norm_species, "category": category, "cut": cut,
            "qty": lbs, "unit": "lbs", "storage": "vacuum_sealed",
        })

    return {
        "species": norm_species,
        "category": category,
        "edible_lbs": round(edible_lbs, 1),
        "candidates": candidates,
    }
