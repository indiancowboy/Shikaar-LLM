"""Natural-language entry parsing (build brief §6) — designed for failure.

Three layers: (1) GPT-4o structured extraction, (2) deterministic fallback when
the model is unreachable, (3) the API returns CANDIDATES for human confirm — only
an explicit add commits. This module covers layers 1-2 and the validation/repair
in between; it never raises on bad model output, it drops/repairs instead.
"""
from __future__ import annotations

import json
from typing import Optional

from ..config import GENERATION_MODEL, get_openai
from ..domain import cuts, parsing
from ..domain import species as species_catalog
from ..models import ParseCandidate

_VALID_UNITS = {"lbs", "kg", "pkgs"}

EXTRACTION_SYSTEM = (
    "You extract structured freezer-inventory entries from a hunter's note. "
    "Respond with ONLY a JSON object, no prose, no markdown."
)

EXTRACTION_INSTRUCTIONS = """Return a JSON object: {"entries": [ ... ]}.
Each entry: {"species": string (lowercase, underscores), "category": one of
[__CATEGORIES__], "cut": string,
"qty": number, "unit": one of ["lbs","kg","pkgs"], "storage": one of
["vacuum_sealed","wrapped"], "packs": integer or null, "pack_size": number or null}.

packs: when the note gives a COUNT of packages AND a weight per package, set
"packs" to the count, "pack_size" to the weight of ONE package, "unit" to that
weight's unit, and "qty" to packs * pack_size:
  "10 2 lb packs of ground" -> packs 10, pack_size 2, unit "lbs", qty 20
  "4 roasts about 3 lbs each" -> packs 4, pack_size 3, unit "lbs", qty 12
  "3 packs of steaks totaling 6 lbs" -> packs 3, pack_size 2, unit "lbs", qty 6
Count with no weight -> packs null, unit "pkgs", qty = the count ("two backstraps").
Weight with no count -> packs null, qty = the weight ("8 lbs ground").

species + category: use the species key from this list when the animal is on
it ("bull elk" -> elk, "snow geese" -> snow_goose); otherwise a short lowercase
name and the closest category.
__SPECIES_MAP__
crab cuts: "whole" (whole crabs, cooked or raw), "clusters" (legs/claws), or
"picked meat"; shrimp/lobster/crawfish: "whole" or "tails".

- one entry per distinct cut; "shoulder roast" is ONE entry, not shoulder + roast
- normalize: "back straps"->backstrap, "the rest ground"->ground, "loins into steaks"->steaks
- vague amounts (few/some/a couple/the rest) -> sensible estimate; none stated -> 1
- default storage vacuum_sealed unless wrapped / butcher paper / freezer paper
"""
EXTRACTION_INSTRUCTIONS = (
    EXTRACTION_INSTRUCTIONS
    .replace("__CATEGORIES__", ",".join(f'"{c}"' for c in species_catalog.CATEGORIES))
    .replace("__SPECIES_MAP__", species_catalog.prompt_category_map())
)


def _llm_extract(text: str) -> list[dict]:
    """One model attempt. Returns a list of raw entry dicts or raises."""
    resp = get_openai().chat.completions.create(
        model=GENERATION_MODEL,
        max_tokens=1000,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": EXTRACTION_SYSTEM},
            {"role": "user", "content": f'{EXTRACTION_INSTRUCTIONS}\n\nNote: "{text}"'},
        ],
    )
    raw = (resp.choices[0].message.content or "").strip()
    data = json.loads(raw)
    entries = data.get("entries") or data.get("items") or []
    if not isinstance(entries, list) or not entries:
        raise ValueError("no entries")
    return entries


def _num(v, kind):
    """A positive number of `kind` (int/float), or None."""
    try:
        n = kind(v)
    except (TypeError, ValueError):
        return None
    return n if n > 0 else None


def _coerce(o: dict, *, offline: bool) -> Optional[ParseCandidate]:
    """Validate/repair one raw entry into a ParseCandidate, or drop it (None)."""
    if not isinstance(o, dict):
        return None
    species = str(o.get("species", "")).lower().strip().replace(" ", "_")
    if not species:
        return None

    # Snap to the catalog key when we know the animal ("wild boar" -> wild_hog).
    category = o.get("category") or o.get("cat")
    known = species_catalog.lookup(species)
    if known:
        species = known.key
        if category not in parsing._VALID_CATEGORIES:
            category = known.category
    if category not in parsing._VALID_CATEGORIES:
        category = "biggame"

    cut = str(o.get("cut") or "whole / mixed").strip() or "whole / mixed"

    try:
        qty = float(o.get("qty", 1))
    except (TypeError, ValueError):
        qty = 1.0
    if qty <= 0:
        qty = 1.0

    unit = o.get("unit") if o.get("unit") in _VALID_UNITS else "lbs"
    storage = "wrapped" if o.get("storage") == "wrapped" else "vacuum_sealed"

    # Packs are kept only when both count and per-pack weight are usable; the
    # total is recomputed from them rather than trusting the model's arithmetic.
    packs, pack_size = _num(o.get("packs"), int), _num(o.get("pack_size"), float)
    if packs and pack_size:
        if unit == "pkgs":
            unit = "lbs"
        qty = round(packs * pack_size, 3)
    elif packs and unit == "pkgs":
        qty, packs, pack_size = float(packs), None, None
    else:
        packs = pack_size = None
    qty, packs, pack_size = cuts.default_packs(category, cut, species, qty, unit, packs, pack_size)

    try:
        return ParseCandidate(
            species=species, category=category, cut=cut, qty=qty,
            unit=unit, storage=storage, packs=packs, pack_size=pack_size,
            parsed_offline=offline,
        )
    except Exception:
        return None


def coerce_all(raw: list[dict], *, offline: bool) -> list[ParseCandidate]:
    return [c for c in (_coerce(o, offline=offline) for o in raw) if c is not None]


def parse_text(text: str, *, attempts: int = 3) -> list[ParseCandidate]:
    """Layer 1 -> Layer 2. Returns candidates (never raises on model trouble)."""
    text = (text or "").strip()
    if not text:
        return []

    raw: Optional[list[dict]] = None
    for _ in range(attempts):
        try:
            raw = _llm_extract(text)
            break
        except Exception:
            raw = None

    offline = False
    if raw is None:
        raw = parsing.fallback_parse(text)  # model unreachable -> parse locally
        offline = bool(raw)

    return coerce_all(raw, offline=offline)
