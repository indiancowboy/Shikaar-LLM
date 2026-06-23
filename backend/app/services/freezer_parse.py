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
from ..domain import parsing
from ..models import ParseCandidate

_VALID_UNITS = {"lbs", "kg", "pkgs"}

EXTRACTION_SYSTEM = (
    "You extract structured freezer-inventory entries from a hunter's note. "
    "Respond with ONLY a JSON object, no prose, no markdown."
)

EXTRACTION_INSTRUCTIONS = """Return a JSON object: {"entries": [ ... ]}.
Each entry: {"species": string (lowercase, underscores), "category": one of
["biggame","hog","bear","waterfowl","upland","fishlean","fishoily"], "cut": string,
"qty": number, "unit": one of ["lbs","kg","pkgs"], "storage": one of
["vacuum_sealed","wrapped"]}.

category map: deer/elk/nilgai/antelope=biggame; hog/boar=hog; bear=bear;
duck/goose/teal=waterfowl; dove/quail/pheasant/turkey=upland;
redfish/catfish/bass/walleye/snapper=fishlean; salmon/mackerel/tuna=fishoily.

- one entry per distinct cut; "shoulder roast" is ONE entry, not shoulder + roast
- normalize: "back straps"->backstrap, "the rest ground"->ground, "loins into steaks"->steaks
- vague amounts (few/some/a couple/the rest) -> sensible estimate; none stated -> 1
- default storage vacuum_sealed unless wrapped / butcher paper / freezer paper
"""


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


def _coerce(o: dict, *, offline: bool) -> Optional[ParseCandidate]:
    """Validate/repair one raw entry into a ParseCandidate, or drop it (None)."""
    if not isinstance(o, dict):
        return None
    species = str(o.get("species", "")).lower().strip().replace(" ", "_")
    if not species:
        return None

    category = o.get("category") or o.get("cat")
    if category not in parsing._VALID_CATEGORIES:
        category = parsing.category_for(species) or "biggame"

    cut = str(o.get("cut") or "whole / mixed").strip() or "whole / mixed"

    try:
        qty = float(o.get("qty", 1))
    except (TypeError, ValueError):
        qty = 1.0
    if qty <= 0:
        qty = 1.0

    unit = o.get("unit") if o.get("unit") in _VALID_UNITS else "lbs"
    storage = "wrapped" if o.get("storage") == "wrapped" else "vacuum_sealed"

    try:
        return ParseCandidate(
            species=species, category=category, cut=cut, qty=qty,
            unit=unit, storage=storage, parsed_offline=offline,
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
