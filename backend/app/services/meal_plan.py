"""Meal planner (build brief §9) — plans meals around the freezer inventory.

Reads inventory, sorts by urgency, retrieves recipes biased to species/cuts on
hand (especially aging-out ones), and generates ~3 meals in the TBGH voice that
lead with whatever needs cooking first.
"""
from __future__ import annotations

from typing import Optional

from ..domain import shelf_life
from ..models import FreezerItem
from ..rag import generation, retrieval

_PROMPT = """You are Shikaar (Two Brown Guys Hunt). Plan 3 meals from this freezer manifest.
Lead with PAST_PRIME / USE_SOON items. Name a specific dish per meal + one line why it
fits the cut. Work an Indian/fusion spice angle into at least one. Encouraging, no preamble.
Under 220 words.

Manifest (most urgent first):
{manifest}

Retrieved recipes:
{rag_context}
"""


def _graded(items: list[FreezerItem]) -> list[tuple[dict, FreezerItem]]:
    g = [(shelf_life.freshness(it.category, it.storage, it.date_frozen), it) for it in items]
    g.sort(key=lambda x: x[0]["pct"], reverse=True)
    return g


def meal_plan(items: list[FreezerItem], *, query: Optional[str] = None) -> dict:
    """Return {"plan": str, "manifest": [...]} or a calm empty-state message."""
    if not items:
        return {"plan": "Nothing in the freezer yet — log a few items and I'll plan around them.", "manifest": []}

    graded = _graded(items)
    manifest_lines = []
    for fresh, it in graded:
        manifest_lines.append(
            f"- {it.qty}{it.unit} {it.species.replace('_', ' ')} {it.cut} "
            f"— {fresh['age_months']}mo old, status {fresh['status'].upper()}"
        )
    manifest = "\n".join(manifest_lines)

    # Bias retrieval toward what's on hand, weighting the most-urgent items.
    urgent = [it for fresh, it in graded if fresh["status"] in ("past_prime", "use_soon")]
    focus = urgent or [it for _, it in graded]
    retrieval_query = (query or "") + " " + " ".join(
        f"{it.species} {it.cut}".replace("_", " ") for it in focus[:5]
    )
    matches = retrieval.retrieve(retrieval_query.strip(), top_k=6, content_type="recipe")
    rag_context = retrieval.format_context(matches)

    plan = generation.generate(_PROMPT.format(manifest=manifest, rag_context=rag_context))
    return {
        "plan": plan,
        "manifest": [{"item": it.with_status().model_dump()} for _, it in graded],
    }
