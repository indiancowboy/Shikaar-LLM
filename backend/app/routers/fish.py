"""Fish species reference endpoints (FishBase-derived snapshot)."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..services import fish_species

router = APIRouter(prefix="/fish", tags=["fish"])


@router.get("")
def list_fish() -> dict:
    return {"species": fish_species.list_all()}


@router.get("/{name}")
def get_fish(name: str) -> dict:
    rec = fish_species.lookup(name)
    if rec is None:
        raise HTTPException(status_code=404, detail=f"no species reference for '{name}'")
    return rec
