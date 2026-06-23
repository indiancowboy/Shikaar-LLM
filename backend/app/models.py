"""Pydantic models — the backend's data contracts (build brief §3, §10).

Computed fields (status, age_months) are derived server-side via the
shelf_life domain module, never trusted from the client.
"""
from __future__ import annotations

from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

from .domain import shelf_life

Category = Literal[
    "biggame", "hog", "bear", "waterfowl", "upland", "fishlean", "fishoily"
]
Unit = Literal["lbs", "kg", "pkgs"]
Storage = Literal["vacuum_sealed", "wrapped"]
Status = Literal["prime", "good", "use_soon", "past_prime"]


class FreezerItemBase(BaseModel):
    species: str  # lowercase, underscores, e.g. "whitetail", "wild_hog", "black_bear"
    category: Category  # drives shelf life
    cut: str  # "backstrap", "ground", "fillets", "shoulder roast"
    qty: float = Field(gt=0)
    unit: Unit
    storage: Storage
    date_frozen: date
    harvest_location: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("date_frozen")
    @classmethod
    def _not_future(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("date_frozen cannot be in the future")
        return v

    @field_validator("species", "cut")
    @classmethod
    def _non_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("must not be empty")
        return v


class FreezerItemCreate(FreezerItemBase):
    """Payload for POST /freezer (manual add)."""


class FreezerItemUpdate(BaseModel):
    """Payload for PATCH /freezer/{id} — all fields optional. The merged result
    is re-validated against FreezerItem, so cross-field rules (no future date)
    still apply on update."""

    species: Optional[str] = None
    category: Optional[Category] = None
    cut: Optional[str] = None
    qty: Optional[float] = Field(default=None, gt=0)
    unit: Optional[Unit] = None
    storage: Optional[Storage] = None
    date_frozen: Optional[date] = None
    harvest_location: Optional[str] = None
    notes: Optional[str] = None


class FreezerItem(FreezerItemBase):
    """A stored item with its server-generated id."""

    id: str

    def with_status(self) -> "FreezerItemRead":
        """Attach server-computed freshness fields."""
        fresh = shelf_life.freshness(self.category, self.storage, self.date_frozen)
        return FreezerItemRead(
            **self.model_dump(),
            status=fresh["status"],
            age_months=fresh["age_months"],
            pct=fresh["pct"],
            shelf_life_months=fresh["shelf_life_months"],
        )


class FreezerItemRead(FreezerItem):
    """What the API returns — item plus computed freshness (brief §10)."""

    status: Status
    age_months: float
    pct: float
    shelf_life_months: int


class ParseCandidate(BaseModel):
    """An un-committed entry produced by the parse pipelines (brief §6, §7).

    `parsed_offline` flags the deterministic-fallback / OCR path so the UI can
    warn the user to look closely before committing.
    """

    species: str
    category: Category
    cut: str
    qty: float = Field(gt=0)
    unit: Unit
    storage: Storage
    parsed_offline: bool = False
