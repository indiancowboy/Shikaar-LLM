"""Deterministic fallback parser + species/cut lexicons (build brief §6, Layer 2).

This is the safety net: when the LLM extraction can't be reached or fails, we
parse locally with keyword matching so the feature NEVER hard-fails. Ported from
the prototype's `fallbackParse`. Key rules:
  - compound cuts ("shoulder roast") are listed before their parts so they win
  - each cut is attributed to the nearest preceding species
  - a named species with no cut found is logged as "whole / mixed" — never
    silently dropped
Pure / offline — no network, fully unit-testable.
"""
from __future__ import annotations

import re

from . import species as species_catalog

# Compound cuts before their parts so "shoulder roast" matches as one entry.
CUT_LEX: list[tuple[list[str], str]] = [
    (["shoulder roast"], "shoulder roast"),
    (["ham roast"], "ham roast"),
    (["picked meat", "crab meat", "lump meat"], "picked meat"),
    (["cluster", "claw"], "clusters"),
    (["tails"], "tails"),
    (["back strap", "backstrap"], "backstrap"),
    (["tenderloin"], "tenderloin"),
    (["sausage"], "sausage"),
    (["ground", "burger", "mince"], "ground"),
    (["steak"], "steaks"),
    (["roast"], "roasts"),
    (["belly"], "belly"),
    (["shoulder"], "shoulder"),
    (["shank"], "shanks"),
    (["rib"], "ribs"),
    (["breast"], "breasts"),
    (["fillet", "filet"], "fillets"),
    (["loin"], "loin"),
    (["wing"], "wings"),
    (["leg", "thigh", "quarter"], "legs"),
]

QTY_WORDS = {
    "a couple": 2, "couple": 2, "a few": 2, "few": 2, "several": 3,
    "some": 2, "a little": 1, "little": 1, "dozen": 12, "the rest": 1,
}

_VALID_CATEGORIES = set(species_catalog.CATEGORIES)

# Uniform packs written just before a cut: "10 2 lb packs of", "10 x 2lb packs",
# "10 packs of 2 lb". Group 1 = pack count, group 2 = weight per pack.
_PACK_PATTERNS = [
    re.compile(
        r"(\d+)\s*(?:x\s*)?(\d+(?:\.\d+)?)\s*-?\s*(?:lbs?|pounds?|#)\s*"
        r"(?:packs?|pkgs?|packages?|bags?)\s*(?:of\s*)?$"
    ),
    re.compile(
        r"(\d+)\s*(?:packs?|pkgs?|packages?|bags?)\s*(?:of\s*)?(?:about\s*|~\s*)?"
        r"(\d+(?:\.\d+)?)\s*-?\s*(?:lbs?|pounds?|#)\s*(?:each\s*)?(?:of\s*)?$"
    ),
]


def _pack_before(t: str, i: int) -> tuple[int, float] | None:
    """(packs, pack_size) if a uniform-pack phrase ends right before index i."""
    pre = t[max(0, i - 32):i]
    for pat in _PACK_PATTERNS:
        m = pat.search(pre)
        if m:
            packs, size = int(m.group(1)), float(m.group(2))
            if packs > 0 and size > 0:
                return packs, size
    return None


def category_for(species: str) -> str | None:
    """Best-effort category for a (possibly messy) species string."""
    hit = species_catalog.lookup(species)
    return hit.category if hit else None


def fallback_parse(text: str) -> list[dict]:
    """Parse freezer entries from text with no model. Returns candidate dicts
    shaped like ParseCandidate (without `parsed_offline`, set by the caller)."""
    t = text.lower()

    # Locate every species mention, ordered by position.
    sp: list[dict] = [
        {"i": i, "species": hit.key, "category": hit.category}
        for i, hit in species_catalog.find_all(t)
    ]
    if not sp:
        return []

    storage = "wrapped" if re.search(r"wrapped|butcher paper|freezer paper", t) else "vacuum_sealed"

    found: list[dict] = []
    used = [False] * len(t)
    for kws, cut in CUT_LEX:
        for k in kws:
            start = 0
            while True:
                i = t.find(k, start)
                if i == -1:
                    break
                if not any(used[i:i + len(k)]):
                    for j in range(i, i + len(k)):
                        used[j] = True
                    # a species written right after the cut ("ground goat")
                    # owns it; otherwise the nearest species before it
                    after = next((s for s in sp if i + len(k) < s["i"] <= i + len(k) + 2), None)
                    owner = after or sp[0]
                    if after is None:
                        for s in sp:
                            if s["i"] <= i:
                                owner = s
                            else:
                                break
                    packed = _pack_before(t, i)
                    if packed:
                        packs, size = packed
                        found.append({
                            "i": i, "species": owner["species"], "category": owner["category"],
                            "cut": cut, "qty": packs * size, "unit": "lbs",
                            "storage": storage, "packs": packs, "pack_size": size,
                        })
                        start = i + len(k)
                        continue
                    pre = t[max(0, i - 16):i]
                    qty = 1.0
                    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:lbs?|pounds?|packs?|pkgs?)?\s*$", pre)
                    if m:
                        qty = float(m.group(1))
                    else:
                        for w, val in QTY_WORDS.items():
                            if w in pre:
                                qty = float(val)
                                break
                    is_weight = bool(re.search(r"lb|pound", pre))
                    found.append({
                        "i": i, "species": owner["species"], "category": owner["category"],
                        "cut": cut, "qty": qty, "unit": "lbs" if is_weight else "pkgs",
                        "storage": storage,
                    })
                start = i + len(k)

    # Any species with no cut captured -> log whole, so nothing is dropped.
    covered = {f["species"] for f in found}
    seen: set[str] = set()
    for s in sp:
        if s["species"] not in covered and s["species"] not in seen:
            seen.add(s["species"])
            found.append({
                "i": s["i"], "species": s["species"], "category": s["category"],
                "cut": "whole / mixed", "qty": 1.0, "unit": "lbs", "storage": storage,
            })

    if not found:
        return [
            {"species": s["species"], "category": s["category"], "cut": "whole / mixed",
             "qty": 1.0, "unit": "lbs", "storage": storage}
            for s in sp
        ]

    found.sort(key=lambda x: x["i"])
    return [{k: v for k, v in f.items() if k != "i"} for f in found]
