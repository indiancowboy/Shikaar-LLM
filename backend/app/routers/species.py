"""Species catalog for the UI (manual-entry suggestions + category picker)."""
from __future__ import annotations

from fastapi import APIRouter

from ..domain import species as species_catalog

router = APIRouter(prefix="/species", tags=["species"])


@router.get("")
def list_species() -> dict:
    return {
        "species": [
            {"key": s.key, "label": s.label, "aliases": list(s.aliases),
             "category": s.category, "group": s.group}
            for s in species_catalog.catalog()
        ],
        "categories": [
            {"key": k, "label": label, "hint": hint}
            for k, (label, hint) in species_catalog.CATEGORIES.items()
        ],
    }
