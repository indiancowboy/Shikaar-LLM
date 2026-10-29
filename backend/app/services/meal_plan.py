"""Meal planner (build brief §9) — plans meals around the freezer inventory.

Two stages so suggestions can't drift off what's actually in the freezer:

1. **Match (deterministic).** Recipes come from the tagged TBGH library and are
   shortlisted by protein category + cut type (see services/recipes.py). A steak
   recipe never reaches the model for a pack of ground meat; a sausage recipe
   reaches it for ground meat only with the "season it into sausage" prep note.
2. **Plan (model).** The model picks meals from that shortlist — or invents a
   creative dish, borrowing a flavor base from the cuisine profiles — and returns
   structured JSON. Every meal is validated against the freezer and the
   shortlist; invalid meals are dropped and the model is asked again once.

Library meals carry the full TBGH recipe text verbatim; creative meals carry
model-written ingredients and steps.
"""
from __future__ import annotations

from typing import Optional

from ..domain import shelf_life
from ..domain.cuts import cut_type_for
from ..models import FreezerItem
from ..rag import generation, retrieval
from . import recipes

_PROMPT = """Plan {n} dinners for the week from this freezer. Reply with ONLY a JSON object.

# Freezer (most urgent first). [id] amount species cut — cut type — age, status
{manifest}

# TBGH recipe library — ONLY these recipes fit what's in the freezer.
# Each lists the freezer item ids it fits. "adapt" fits need the stated prep step.
{recipes}

# Regional cuisine profiles (flavor bases to borrow for creative dishes)
{cuisines}

# Technique notes
{techniques}
{request}
# Rules
- Lead with PAST_PRIME / USE_SOON items.
- A "library" meal MUST use a recipe id from the library list above, and only
  with freezer item ids listed as fitting that recipe. If the fit is "adapt",
  "adaptation" must spell out the prep step in one or two sentences.
- A "creative" meal invents a dish from a cuisine profile. Its method MUST suit
  the cut type: ground -> keema, kebabs, meatballs, patties, fillings, sauces;
  sausage -> crumbled or sliced; tender -> fast and hot (sear, grill), never a
  long braise; braise -> low and slow; breast -> quick sear or slice-and-fry;
  fillet -> pan, grill, poach or curry. Write a real recipe: ingredients with
  quantities, and numbered steps with times and doneness temps (wild hog and
  bear: 160°F; ground game: 160°F).
- Never describe an ingredient that isn't in the freezer as if it were (ground
  meat is not "sausage" unless the adaptation says to season it).
- At least one creative meal when the freezer allows. No repeated dishes.
- "uses": the freezer item ids and how many packs to thaw (null for items
  without packs). Don't use more packs than an item has.
- "why": one or two concrete sentences on why it suits that cut. No filler.

# JSON shape
{{"meals": [{{
  "title": "Dish name",
  "kind": "library" | "creative",
  "recipe_id": "recipe id from the library list" | null,
  "cuisine": "cuisine profile drawn from" | null,
  "uses": [{{"item_id": "itm_...", "packs": 1}}],
  "why": "...",
  "adaptation": "..." | null,
  "time": "about 40 min",
  "serves": "4",
  "ingredients": ["1 lb ground wild boar", "..."],
  "steps": ["...", "..."]
}}]}}
For library meals leave "ingredients" and "steps" empty — the recipe is shown verbatim.
"""

_NONE = "(none)"
_MAX_LIBRARY = 10


def _graded(items: list[FreezerItem]) -> list[tuple[dict, FreezerItem]]:
    g = [(shelf_life.freshness(it.category, it.storage, it.date_frozen), it) for it in items]
    g.sort(key=lambda x: x[0]["pct"], reverse=True)
    return g


def amount_label(it: FreezerItem) -> str:
    if it.packs is not None:
        return f"{it.packs} packs × {it.pack_size:g} {it.unit} ({it.qty:g} {it.unit})"
    return f"{it.qty:g} {it.unit}"


def _manifest(graded: list[tuple[dict, FreezerItem]]) -> str:
    return "\n".join(
        f"- [{it.id}] {amount_label(it)} {it.species.replace('_', ' ')} {it.cut} — "
        f"{cut_type_for(it.category, it.cut) or 'unknown cut'} — "
        f"{fresh['age_months']}mo old, {fresh['status'].upper()}"
        for fresh, it in graded
    )


def _library_block(cands: dict[str, dict]) -> str:
    blocks = []
    for rid, c in list(cands.items())[:_MAX_LIBRARY]:
        fits = ", ".join(
            f"[{f['item_id']}] " + ("exact" if f["kind"] == "exact" else f"adapt: {f['note']}")
            for f in c["fits"]
        )
        blocks.append(f"## id: {rid} — {c['recipe']['title']}\nFits: {fits}\n{recipes.summary(c['recipe'])}")
    return "\n\n".join(blocks) or "(no library recipe fits this freezer — make every meal creative)"


def _context(query: str, content_type: str, top_k: int) -> str:
    """Cuisine/technique inspiration from the vector index. Optional: the plan
    still works if the index is unreachable."""
    try:
        return retrieval.format_context(retrieval.retrieve(query, top_k=top_k, content_type=content_type)) or _NONE
    except Exception:
        return _NONE


def _str(v) -> Optional[str]:
    return v.strip() if isinstance(v, str) and v.strip() else None


def _str_list(v) -> list[str]:
    return [s.strip() for s in v if isinstance(s, str) and s.strip()] if isinstance(v, list) else []


def _validate(data: dict, by_id: dict[str, FreezerItem], cands: dict[str, dict], n: int) -> list[dict]:
    """Keep only meals that use real freezer items and, for library meals, a
    shortlisted recipe that actually fits those items."""
    meals: list[dict] = []
    seen: set[str] = set()
    for m in data.get("meals") or []:
        if not isinstance(m, dict):
            continue
        title = _str(m.get("title"))
        if not title or title.lower() in seen:
            continue

        uses = []
        for u in m.get("uses") or []:
            item = by_id.get(u.get("item_id")) if isinstance(u, dict) else None
            if item is None or any(x["item_id"] == item.id for x in uses):
                continue
            packs = None
            if item.packs is not None:
                try:
                    packs = max(1, min(int(u.get("packs") or 1), item.packs))
                except (TypeError, ValueError):
                    packs = 1
            uses.append({"item_id": item.id, "packs": packs})
        if not uses:
            continue

        meal = {
            "title": title,
            "why": _str(m.get("why")) or "",
            "time": _str(m.get("time")),
            "serves": _str(str(m.get("serves"))) if m.get("serves") is not None else None,
            "uses": uses,
            "adaptation": _str(m.get("adaptation")),
            "cuisine": _str(m.get("cuisine")),
            "recipe": None,
            "ingredients": [],
            "steps": [],
        }

        if m.get("kind") == "library":
            cand = cands.get(m.get("recipe_id"))
            if cand is None:
                continue
            fits = {f["item_id"]: f for f in cand["fits"]}
            if any(u["item_id"] not in fits for u in uses):
                continue
            notes = [fits[u["item_id"]]["note"] for u in uses if fits[u["item_id"]]["kind"] == "adapt"]
            if notes and not meal["adaptation"]:
                meal["adaptation"] = " ".join(notes)
            r = cand["recipe"]
            meal.update(kind="library", recipe={
                "id": r["id"], "title": r["title"], "text": r["text"],
                "prep_time": r["prep_time"], "cook_time": r["cook_time"],
            })
        else:
            ingredients, steps = _str_list(m.get("ingredients")), _str_list(m.get("steps"))
            if len(ingredients) < 3 or len(steps) < 2:
                continue
            meal.update(kind="creative", ingredients=ingredients, steps=steps)

        seen.add(title.lower())
        meals.append(meal)
        if len(meals) == n:
            break
    return meals


def _as_text(meals: list[dict], by_id: dict[str, FreezerItem]) -> str:
    """Plain-text rendering (kept for clients that only read `plan`)."""
    lines = []
    for i, m in enumerate(meals, 1):
        label = "TBGH recipe" if m["kind"] == "library" else f"Creative{' · ' + m['cuisine'] if m['cuisine'] else ''}"
        used = ", ".join(
            f"{u['packs']} pack{'s' if u['packs'] != 1 else ''} {by_id[u['item_id']].species.replace('_', ' ')} {by_id[u['item_id']].cut}"
            if u["packs"] else f"{by_id[u['item_id']].species.replace('_', ' ')} {by_id[u['item_id']].cut}"
            for u in m["uses"]
        )
        lines.append(f"Meal {i}: {m['title']} ({label})\nUses: {used}\n{m['why']}")
        if m["adaptation"]:
            lines.append(f"Prep: {m['adaptation']}")
        lines.append("")
    return "\n".join(lines).strip()


def meal_plan(items: list[FreezerItem], *, query: Optional[str] = None, attempts: int = 2) -> dict:
    """Return {"plan": str, "meals": [...], "manifest": [...]}."""
    if not items:
        return {"plan": "Nothing in the freezer yet — log a few items and I'll plan around them.",
                "meals": [], "manifest": []}

    graded = _graded(items)
    ordered = [it for _, it in graded]
    by_id = {it.id: it for it in ordered}
    cands = recipes.candidates(ordered)
    n = 3

    focus = [it for fresh, it in graded if fresh["status"] in ("past_prime", "use_soon")] or ordered
    rq = ((query or "") + " " + " ".join(f"{it.species} {it.cut}".replace("_", " ") for it in focus[:5])).strip()

    prompt = _PROMPT.format(
        n=n,
        manifest=_manifest(graded),
        recipes=_library_block(cands),
        cuisines=_context(rq, "cuisine", 3),
        techniques=_context(rq, "technique", 2),
        request=f"\n# Cook's request\n{query.strip()}\n" if query and query.strip() else "",
    )

    meals: list[dict] = []
    for _ in range(attempts):
        try:
            data = generation.generate_json(prompt, max_tokens=3000, temperature=0.6)
        except Exception:
            continue
        meals = _validate(data, by_id, cands, n)
        if meals:
            break

    plan = _as_text(meals, by_id) if meals else "Couldn't put a plan together just now — try again in a minute."
    return {
        "plan": plan,
        "meals": meals,
        "manifest": [{"item": it.with_status().model_dump()} for it in ordered],
    }
