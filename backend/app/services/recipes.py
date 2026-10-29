"""Recipe library + cut-aware matching against the freezer.

The library is the TBGH recipe set baked into app/reference/recipes.json (see
build_recipe_catalog.py). A recipe fits a freezer item when the item's category
is one the recipe is tagged for AND the item's cut type matches one the recipe
needs — exactly, or via a known conversion (ground -> sausage, ...), which comes
with the prep note the cook needs. No text similarity, no network.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from ..domain.cuts import cut_type_for, match_kind
from ..models import FreezerItem

_CATALOG = Path(__file__).resolve().parent.parent / "reference" / "recipes.json"


@lru_cache(maxsize=1)
def catalog() -> dict[str, dict]:
    """recipe id -> recipe entry."""
    return {r["id"]: r for r in json.loads(_CATALOG.read_text(encoding="utf-8"))}


def get(recipe_id: str) -> dict | None:
    return catalog().get(recipe_id)


def matches_for_item(item: FreezerItem) -> list[dict]:
    """Recipes that fit one item, exact fits first: [{recipe, kind, note}]."""
    ct = cut_type_for(item.category, item.cut, item.species)
    out = []
    for recipe in catalog().values():
        if item.category not in recipe["categories"]:
            continue
        kind, note = match_kind(ct, recipe["cuts"])
        if kind:
            out.append({"recipe": recipe, "kind": kind, "note": note})
    out.sort(key=lambda m: (m["kind"] != "exact", m["recipe"]["title"]))
    return out


def candidates(items: list[FreezerItem]) -> dict[str, dict]:
    """Every recipe that fits at least one item, in the order the items are
    given (pass them most-urgent first): recipe id -> {recipe, fits: [{item_id,
    kind, note}]}."""
    out: dict[str, dict] = {}
    for item in items:
        for m in matches_for_item(item):
            rid = m["recipe"]["id"]
            entry = out.setdefault(rid, {"recipe": m["recipe"], "fits": []})
            entry["fits"].append({"item_id": item.id, "kind": m["kind"], "note": m["note"]})
    return out


def summary(recipe: dict, limit: int = 900) -> str:
    """Description + ingredients excerpt for the model (not the full method)."""
    text = recipe["text"]
    cut = len(text)
    for marker in ("\nPreparation", "\nInstructions", "\n## Preparation", "\n## Instructions", "\n**Preparation", "\n**Instructions"):
        i = text.find(marker)
        if i != -1:
            cut = min(cut, i)
    return text[:min(cut, limit)].strip()
