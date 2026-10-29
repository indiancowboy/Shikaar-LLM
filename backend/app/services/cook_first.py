"""Cook First (build brief §8) — proactive recipe surfacing.

Surfaces the 2-3 most-urgent items (past_prime / use_soon first), each with
TBGH library recipes that fit that item's protein and cut (services/recipes.py),
exact fits first. Hides itself when nothing is urgent.
"""
from __future__ import annotations

from ..domain import shelf_life
from ..models import FreezerItem
from . import recipes

_URGENT = {"past_prime", "use_soon"}


def cook_first(items: list[FreezerItem], *, limit: int = 3, suggestions_per_item: int = 3) -> dict:
    """Return {"urgent": bool, "cards": [...]}.

    Each card: the item (with computed status) + titles of library recipes that
    fit it.
    """
    graded = [
        (shelf_life.freshness(it.category, it.storage, it.date_frozen), it)
        for it in items
    ]
    urgent = [g for g in graded if g[0]["status"] in _URGENT]
    urgent.sort(key=lambda g: g[0]["pct"], reverse=True)

    cards = []
    for fresh, item in urgent[:limit]:
        matches = recipes.matches_for_item(item)[:suggestions_per_item]
        cards.append({
            "item": item.with_status().model_dump(),
            "suggestions": [m["recipe"]["title"] for m in matches],
        })

    return {"urgent": bool(cards), "cards": cards}
