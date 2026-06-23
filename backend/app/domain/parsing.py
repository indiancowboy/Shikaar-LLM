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

# (keywords, canonical species, category). Compound/longer keywords help, but
# attribution is by position so duplicates within a species are harmless.
SPECIES_LEX: list[tuple[list[str], str, str]] = [
    (["whitetail", "white tail", "mule deer", "muley", "deer", "venison"], "whitetail", "biggame"),
    (["elk"], "elk", "biggame"),
    (["nilgai"], "nilgai", "biggame"),
    (["antelope", "pronghorn"], "antelope", "biggame"),
    (["black bear", "bear"], "black_bear", "bear"),
    (["hog", "boar", "feral pig", "wild pig"], "wild_hog", "hog"),
    (["mallard", "duck"], "duck", "waterfowl"),
    (["teal"], "teal", "waterfowl"),
    (["goose"], "goose", "waterfowl"),
    (["dove"], "dove", "upland"),
    (["quail"], "quail", "upland"),
    (["pheasant"], "pheasant", "upland"),
    (["turkey"], "turkey", "upland"),
    (["redfish", "red fish"], "redfish", "fishlean"),
    (["catfish"], "catfish", "fishlean"),
    (["walleye"], "walleye", "fishlean"),
    (["snapper"], "snapper", "fishlean"),
    (["bass"], "bass", "fishlean"),
    (["salmon"], "salmon", "fishoily"),
    (["mackerel"], "mackerel", "fishoily"),
    (["tuna"], "tuna", "fishoily"),
]

# Compound cuts before their parts so "shoulder roast" matches as one entry.
CUT_LEX: list[tuple[list[str], str]] = [
    (["shoulder roast"], "shoulder roast"),
    (["ham roast"], "ham roast"),
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

_VALID_CATEGORIES = {
    "biggame", "hog", "bear", "waterfowl", "upland", "fishlean", "fishoily",
}


def category_for(species: str) -> str | None:
    """Best-effort category for a (possibly messy) species string."""
    s = species.lower().replace("_", " ").strip()
    canon = species.lower().replace(" ", "_")
    for kws, sp, cat in SPECIES_LEX:
        if sp == canon:
            return cat
        for k in kws:
            if k in s:
                return cat
    return None


def fallback_parse(text: str) -> list[dict]:
    """Parse freezer entries from text with no model. Returns candidate dicts
    shaped like ParseCandidate (without `parsed_offline`, set by the caller)."""
    t = text.lower()

    # Locate every species mention, ordered by position.
    sp: list[dict] = []
    for kws, species, cat in SPECIES_LEX:
        for k in kws:
            i = t.find(k)
            if i > -1:
                sp.append({"i": i, "species": species, "category": cat})
    sp.sort(key=lambda x: x["i"])
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
                    # nearest species at or before this cut
                    owner = sp[0]
                    for s in sp:
                        if s["i"] <= i:
                            owner = s
                        else:
                            break
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
