"""Fish-species reference lookup (FishBase-derived, cached locally).

The app reads the curated snapshot at app/reference/fish_species.json — it never
calls the FishBase API in the request path (that API is unreliable; see
backend/fetch_fishbase.py for the offline refresh). Provides name normalization
("redfish" -> red drum / Sciaenops ocellatus) and metadata for fish entries.
"""
from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import Optional

_REFERENCE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "reference", "fish_species.json"
)


def _norm(s: str) -> str:
    return s.lower().strip().replace("_", " ")


@lru_cache(maxsize=1)
def _load() -> tuple[list[dict], dict[str, dict]]:
    """Return (species list, lookup index by every known name/alias)."""
    with open(_REFERENCE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    species = data.get("species", [])
    index: dict[str, dict] = {}
    for rec in species:
        names = {rec["key"], rec["common_name"], rec["scientific_name"], *rec.get("aka", [])}
        for n in names:
            index[_norm(n)] = rec
    return species, index


def lookup(name: str) -> Optional[dict]:
    """Find a species record by key, common name, scientific name, or alias."""
    if not name:
        return None
    _, index = _load()
    return index.get(_norm(name))


def list_all() -> list[dict]:
    species, _ = _load()
    return species


def category_for(name: str) -> Optional[str]:
    """Shikaar lean/oily category for a fish name, if known."""
    rec = lookup(name)
    return rec["category"] if rec else None
