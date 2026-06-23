"""Cook First (build brief §8) — proactive recipe surfacing.

Surfaces the 2-3 most-urgent items (past_prime / use_soon first), each with
recipe suggestions pulled from the REAL RAG knowledge base (no hardcoded dish
lists). Hides itself when nothing is urgent.
"""
from __future__ import annotations

from ..domain import shelf_life
from ..models import FreezerItem
from ..rag import retrieval

_URGENT = {"past_prime", "use_soon"}


def cook_first(items: list[FreezerItem], *, limit: int = 3, suggestions_per_item: int = 3) -> dict:
    """Return {"urgent": bool, "cards": [...]}.

    Each card: the item (with computed status) + a list of suggested recipe
    titles from the KB, biased to that item's species/cut.
    """
    graded = [
        (shelf_life.freshness(it.category, it.storage, it.date_frozen), it)
        for it in items
    ]
    urgent = [g for g in graded if g[0]["status"] in _URGENT]
    urgent.sort(key=lambda g: g[0]["pct"], reverse=True)

    cards = []
    for fresh, item in urgent[:limit]:
        query = f"{item.species} {item.cut} wild game recipe".replace("_", " ")
        matches = retrieval.retrieve(query, top_k=suggestions_per_item, content_type="recipe")
        cards.append({
            "item": item.with_status().model_dump(),
            "suggestions": [m["metadata"].get("title", "Untitled") for m in matches],
        })

    return {"urgent": bool(cards), "cards": cards}
