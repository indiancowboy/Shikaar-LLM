"""Freezer Hub endpoints (build brief §10).

CRUD + the parse/image/yield candidate pipelines + Cook First + meal planner.
Computed fields (status, age_months) are always derived server-side. Parse and
image endpoints return CANDIDATES only — nothing is saved without an explicit
follow-up POST /freezer (the human-confirm step lives on the client).
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from ..domain import yield_profiles
from ..models import (
    FreezerItemCreate,
    FreezerItemRead,
    FreezerItemUpdate,
    ParseCandidate,
)
from ..services import cook_first as cook_first_svc
from ..services import freezer_image, freezer_parse, inventory
from ..services import meal_plan as meal_plan_svc

router = APIRouter(prefix="/freezer", tags=["freezer"])


# ---------------------------------------------------------------- CRUD --------
@router.get("", response_model=list[FreezerItemRead])
def list_freezer() -> list[FreezerItemRead]:
    return [it.with_status() for it in inventory.list_items()]


@router.post("", response_model=FreezerItemRead, status_code=201)
def add_freezer(item: FreezerItemCreate) -> FreezerItemRead:
    return inventory.create(item).with_status()


@router.patch("/{item_id}", response_model=FreezerItemRead)
def edit_freezer(item_id: str, patch: FreezerItemUpdate) -> FreezerItemRead:
    try:
        updated = inventory.update(item_id, patch.model_dump(exclude_unset=True))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    if updated is None:
        raise HTTPException(status_code=404, detail="item not found")
    return updated.with_status()


@router.delete("/{item_id}", status_code=204, response_model=None)
def remove_freezer(item_id: str):
    if not inventory.delete(item_id):
        raise HTTPException(status_code=404, detail="item not found")


# ------------------------------------------------------------- candidates -----
class ParseRequest(BaseModel):
    text: str = Field(min_length=1)


class CandidatesResponse(BaseModel):
    candidates: list[ParseCandidate]
    parsed_offline: bool = False


@router.post("/parse", response_model=CandidatesResponse)
def parse_freezer(req: ParseRequest) -> CandidatesResponse:
    cands = freezer_parse.parse_text(req.text)
    return CandidatesResponse(
        candidates=cands,
        parsed_offline=any(c.parsed_offline for c in cands),
    )


@router.post("/parse-image", response_model=CandidatesResponse)
async def parse_freezer_image(file: UploadFile = File(...)) -> CandidatesResponse:
    data = await file.read()
    if not data:
        raise HTTPException(status_code=422, detail="empty image")
    cands = freezer_image.parse_image(data, file.content_type or "image/jpeg")
    return CandidatesResponse(
        candidates=cands,
        parsed_offline=any(c.parsed_offline for c in cands),
    )


class YieldRequest(BaseModel):
    species: str = Field(min_length=1)
    weight: float = Field(gt=0)
    dressed: bool = False


class YieldResponse(BaseModel):
    species: str
    category: str
    edible_lbs: float
    candidates: list[ParseCandidate]
    note: str = "Estimates — review and adjust before adding."


@router.post("/estimate-yield", response_model=YieldResponse)
def estimate_yield(req: YieldRequest) -> YieldResponse:
    out = yield_profiles.estimate(req.species, req.weight, req.dressed)
    return YieldResponse(
        species=out["species"],
        category=out["category"],
        edible_lbs=out["edible_lbs"],
        candidates=[ParseCandidate(**c) for c in out["candidates"]],
    )


# --------------------------------------------------------- cook / plan --------
@router.get("/cook-first")
def cook_first() -> dict:
    return cook_first_svc.cook_first(inventory.list_items())


class MealPlanRequest(BaseModel):
    query: Optional[str] = None


@router.post("/meal-plan")
def meal_plan(req: Optional[MealPlanRequest] = None) -> dict:
    query = req.query if req else None
    return meal_plan_svc.meal_plan(inventory.list_items(), query=query)
