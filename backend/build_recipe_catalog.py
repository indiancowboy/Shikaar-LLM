"""Build app/reference/recipes.json from the knowledge-base recipe files.

The meal planner matches recipes by their `categories` + `cuts` tags and shows
the full recipe text, so the backend ships its own copy of the recipe library
(the deployed backend only has the `backend/` folder). Re-run after editing any
recipe in knowledge-base/recipes/:

    cd backend && ./venv/bin/python build_recipe_catalog.py

tests/test_recipe_catalog.py fails if the catalog is out of date.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
RECIPES_DIR = HERE.parent / "knowledge-base" / "recipes"
OUT = HERE / "app" / "reference" / "recipes.json"

sys.path.insert(0, str(HERE))
from app.domain.cuts import CUT_TYPES, RECIPE_CATEGORIES  # noqa: E402

_FIELDS = ("title", "protein", "cut", "cuisine", "cooking_method", "difficulty", "prep_time", "cook_time")


def build() -> list[dict]:
    catalog = []
    for path in sorted(RECIPES_DIR.glob("*.md")):
        if path.name.lower() in ("readme.md", "template.md"):
            continue
        m = re.match(r"---\n(.*?)\n---\n", path.read_text(encoding="utf-8"), re.S)
        if not m:
            raise ValueError(f"{path.name}: missing frontmatter")
        meta = yaml.safe_load(m.group(1)) or {}
        body = path.read_text(encoding="utf-8")[m.end():].strip()

        cats, cuts = meta.get("categories") or [], meta.get("cuts") or []
        bad = (set(cats) - RECIPE_CATEGORIES) | (set(cuts) - CUT_TYPES)
        if not cats or not cuts or bad:
            raise ValueError(f"{path.name}: needs valid categories + cuts tags (bad: {sorted(bad)})")

        entry = {"id": path.stem}
        entry.update({k: str(meta.get(k) or "") for k in _FIELDS})
        entry.update({"categories": cats, "cuts": cuts, "text": body})
        catalog.append(entry)
    return catalog


def render(catalog: list[dict]) -> str:
    return json.dumps(catalog, indent=2, ensure_ascii=False) + "\n"


if __name__ == "__main__":
    OUT.write_text(render(build()), encoding="utf-8")
    print(f"wrote {OUT.relative_to(HERE)}")
