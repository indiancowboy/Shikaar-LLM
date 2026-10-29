"""Cut types — the shared vocabulary between freezer items and recipes.

Recipes are tagged in the knowledge base with the cut types they need
(`cuts:` frontmatter) and the freezer categories they suit (`categories:`).
Freezer items carry a free-text cut ("backstrap", "ground", "shoulder roast"),
which `cut_type_for` maps onto the same vocabulary so the meal planner can match
deterministically instead of by text similarity. Pure / offline.
"""
from __future__ import annotations

import re
from typing import Optional

CUT_TYPES = {
    "ground",       # ground / minced meat
    "sausage",      # sausage (already seasoned)
    "tender",       # quick-cook muscle: backstrap, tenderloin, loin, steaks
    "braise",       # slow-cook: roasts, shoulder, shank, ribs, neck, belly, stew
    "breast",       # bird breast
    "legs",         # bird legs / thighs
    "whole_bird",
    "fillet",       # fish fillets, loins, steaks, portions
    "whole_fish",
    "crab_whole",
    "crab_meat",
}

# Recipe categories = freezer categories, plus shellfish (recipes only for now).
RECIPE_CATEGORIES = {
    "biggame", "hog", "bear", "waterfowl", "upland", "fishlean", "fishoily", "shellfish",
}

_FISH = {"fishlean", "fishoily"}
_BIRD = {"waterfowl", "upland"}

# (pattern, cut type), checked in order — compound/specific terms first.
_MEAT_RULES: list[tuple[str, str]] = [
    (r"sausage|brat|chorizo|kielbasa|link", "sausage"),
    (r"ground|mince|burger|keema|grind", "ground"),
    (r"roast|shoulder|shank|rib|neck|belly|brisket|stew|chuck|ham|round", "braise"),
    (r"back ?strap|tenderloin|loin|steak|chop|medallion|filet mignon", "tender"),
]
_BIRD_RULES: list[tuple[str, str]] = [
    (r"sausage", "sausage"),
    (r"ground|mince", "ground"),
    (r"breast", "breast"),
    (r"leg|thigh|quarter|drum|wing", "legs"),
    (r"whole|plucked|dressed|bird", "whole_bird"),
]
_FISH_RULES: list[tuple[str, str]] = [
    (r"ground|mince", "fillet"),   # minced fish starts as fillets
    (r"whole|dressed|gutted", "whole_fish"),
    (r"fillet|filet|loin|steak|portion|side|belly|collar", "fillet"),
]


_CRAB_MEAT = r"meat|picked|lump|claw meat"


def cut_type_for(category: str, cut: str, species: str = "") -> Optional[str]:
    """Map a freezer item's free-text cut to a cut type (None if unknown)."""
    c = (cut or "").lower().replace("_", " ").strip()
    if category == "shellfish":
        # Only crab has library recipes; whole crabs, legs, claws and clusters
        # all cook as "crab_whole". Other shellfish get creative dishes only.
        if "crab" not in f"{species} {c}".lower():
            return None
        return "crab_meat" if re.search(_CRAB_MEAT, c) else "crab_whole"
    # Fish logged without a cut (the parser's "whole / mixed") is almost always fillets.
    if category in _FISH and c in ("", "whole / mixed"):
        return "fillet"
    rules = _FISH_RULES if category in _FISH else _BIRD_RULES if category in _BIRD else _MEAT_RULES
    for pattern, cut_type in rules:
        if re.search(pattern, c):
            return cut_type
    return None


# Item cut type -> recipe cut types it can stand in for, with the prep step the
# cook has to do. (Exact matches need no note.)
CONVERSIONS: dict[tuple[str, str], str] = {
    ("ground", "sausage"): "Season the ground meat into sausage first (salt, sage or fennel, chili flake, a little fat if it's lean).",
    ("sausage", "ground"): "Sausage is already seasoned — ease off the salt and spices in the recipe.",
    ("whole_bird", "breast"): "Break the bird down and use the breasts.",
    ("whole_bird", "legs"): "Break the bird down and use the legs and thighs.",
    ("whole_fish", "fillet"): "Fillet the fish first.",
    ("crab_whole", "crab_meat"): "Cook the crab and pick the meat.",
}


def match_kind(item_cut_type: Optional[str], recipe_cuts: list[str]) -> tuple[Optional[str], Optional[str]]:
    """How an item's cut fits a recipe: ("exact", None), ("adapt", prep note),
    or (None, None) when it doesn't fit."""
    if item_cut_type is None:
        return None, None
    if item_cut_type in recipe_cuts:
        return "exact", None
    for rc in recipe_cuts:
        note = CONVERSIONS.get((item_cut_type, rc))
        if note:
            return "adapt", note
    return None, None
