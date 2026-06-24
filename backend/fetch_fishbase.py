"""
FishBase refresh for Shikaar's fish-species reference.

Pulls scientific facts (max length, family, habitat) from the rOpenSci FishBase
API for the species Shikaar knows about and merges them into
app/reference/fish_species.json. Shikaar's lean/oily `category` is NEVER
overwritten — FishBase doesn't classify fat content; that's our own field.

The live API (fishbase.ropensci.org) is unreliable, so this is an OFFLINE,
run-it-yourself refresh — the app never calls FishBase in the request path. If a
species can't be fetched, its existing curated entry is kept untouched.

Usage:  python fetch_fishbase.py        (writes/updates the reference JSON)
"""

import json
import os
import sys
from urllib.parse import quote
from urllib.request import urlopen

API = "https://fishbase.ropensci.org"
REFERENCE_PATH = os.path.join(
    os.path.dirname(__file__), "app", "reference", "fish_species.json"
)


def _get(path):
    url = f"{API}{path}"
    with urlopen(url, timeout=15) as resp:  # noqa: S310 (trusted host)
        return json.load(resp)


def fetch_species(scientific_name):
    """Return a dict of FishBase facts for a 'Genus species' name, or None."""
    try:
        genus, *rest = scientific_name.split(" ")
        species = rest[0] if rest else ""
        data = _get(f"/species?Genus={quote(genus)}&Species={quote(species)}&limit=1")
        rows = data.get("data") or []
        if not rows:
            return None
        row = rows[0]
        facts = {}
        if row.get("Length"):
            facts["max_length_cm"] = round(float(row["Length"]), 1)
        # FishBase 'Fresh'/'Saltwater'/'Brack' flags -> a coarse habitat string
        env = []
        if row.get("Fresh") == -1:
            env.append("freshwater")
        if row.get("Saltwater") == -1:
            env.append("marine")
        if row.get("Brack") == -1:
            env.append("brackish")
        if env:
            facts["habitat_fishbase"] = "/".join(env)
        return facts
    except Exception as e:  # noqa: BLE001 — best-effort refresh
        print(f"    ! fetch failed for {scientific_name}: {e}")
        return None


def main():
    with open(REFERENCE_PATH, "r", encoding="utf-8") as f:
        ref = json.load(f)

    species = ref.get("species", [])
    print(f"Refreshing {len(species)} species from FishBase ({API}) ...")

    updated = 0
    for rec in species:
        sci = rec.get("scientific_name", "")
        if "spp." in sci or not sci:
            print(f"  - skip {rec['key']} (no single species)")
            continue
        print(f"  · {rec['key']} ({sci})")
        facts = fetch_species(sci)
        if facts:
            rec.update(facts)  # category and curated fields are preserved
            updated += 1

    if updated == 0:
        print("\nNo species updated (API unreachable?). Reference left unchanged.")
        return 1

    with open(REFERENCE_PATH, "w", encoding="utf-8") as f:
        json.dump(ref, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"\nUpdated {updated} species. Wrote {REFERENCE_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
