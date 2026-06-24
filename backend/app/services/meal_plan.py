"""Meal planner (build brief §9) — plans meals around the freezer inventory.

Retrieves across the WHOLE knowledge base — proven TBGH recipes, regional cuisine
profiles, and technique docs — then asks the model to ground in a real recipe when
one fits the cut, and otherwise invent a creative dish by borrowing a flavor base
from a cuisine profile. Leads with whatever's aging out.
"""
from __future__ import annotations

from typing import Optional

from ..domain import shelf_life
from ..models import FreezerItem
from ..rag import generation, retrieval

_PROMPT = """You are Shikaar, the wild-game & fish cooking mind behind Two Brown Guys Hunt
(TBGH). You specialize in wild proteins with a confident Indian/South-Asian spice-fusion lean.

Plan 3 meals for the week from this freezer manifest. Rules:
- LEAD with PAST_PRIME / USE_SOON items — those get cooked first.
- Name a specific dish per meal + a line or two on why it fits that cut/species.
- GROUND in the TBGH recipe library below when a recipe fits the cut — recommend it by
  name and adapt it as needed.
- When no library recipe fits, GET CREATIVE: invent a dish by borrowing a flavor base from
  one of the regional cuisine profiles below (e.g. a Chettinad pepper masala, a Kashmiri
  yakhni, a Bengali mustard/kasundi, a Goan vindaloo) and applying it to the protein on
  hand. Name the cuisine you're drawing from. Use the technique notes for method.
- At least ONE of the three meals should be a creative riff, not a verbatim library recipe.
- Warm, confident, hunting-buddy voice. No preamble, no disclaimers. Under ~250 words.

Manifest (most urgent first):
{manifest}

# TBGH recipe library (proven dishes — adapt when one fits)
{recipes}

# Regional cuisine profiles (flavor inspiration — riff on these to invent dishes)
{cuisines}

# Techniques (handling & cooking methods)
{techniques}
"""

_NONE = "(none retrieved)"


def _graded(items: list[FreezerItem]) -> list[tuple[dict, FreezerItem]]:
    g = [(shelf_life.freshness(it.category, it.storage, it.date_frozen), it) for it in items]
    g.sort(key=lambda x: x[0]["pct"], reverse=True)
    return g


def meal_plan(items: list[FreezerItem], *, query: Optional[str] = None) -> dict:
    """Return {"plan": str, "manifest": [...]} or a calm empty-state message."""
    if not items:
        return {"plan": "Nothing in the freezer yet — log a few items and I'll plan around them.", "manifest": []}

    graded = _graded(items)
    manifest = "\n".join(
        f"- {it.qty}{it.unit} {it.species.replace('_', ' ')} {it.cut} "
        f"— {fresh['age_months']}mo old, status {fresh['status'].upper()}"
        for fresh, it in graded
    )

    # Bias retrieval toward what's on hand, weighting the most-urgent items.
    urgent = [it for fresh, it in graded if fresh["status"] in ("past_prime", "use_soon")]
    focus = urgent or [it for _, it in graded]
    rq = ((query or "") + " " + " ".join(
        f"{it.species} {it.cut}".replace("_", " ") for it in focus[:5]
    )).strip()

    # Retrieve across all three content types so the planner can be creative,
    # not just regurgitate recipes.
    recipes = retrieval.retrieve(rq, top_k=5, content_type="recipe")
    cuisines = retrieval.retrieve(rq, top_k=3, content_type="cuisine")
    techniques = retrieval.retrieve(rq, top_k=2, content_type="technique")

    plan = generation.generate(
        _PROMPT.format(
            manifest=manifest,
            recipes=retrieval.format_context(recipes) or _NONE,
            cuisines=retrieval.format_context(cuisines) or _NONE,
            techniques=retrieval.format_context(techniques) or _NONE,
        ),
        max_tokens=1200,
        temperature=0.85,  # a little more creative than the default
    )
    return {
        "plan": plan,
        "manifest": [{"item": it.with_status().model_dump()} for _, it in graded],
    }
