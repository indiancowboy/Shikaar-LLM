"""In-memory inventory store (build brief §10, §12).

MVP storage. The brief's client persists to localStorage; this server-side store
keeps the CRUD + cook-first + meal-plan endpoints coherent and testable now, and
is the documented seam for the Phase 2 migration to an authenticated DB
(swap this module's body for a real repository; the API contract is unchanged).
"""
from __future__ import annotations

import uuid
from typing import Optional

from ..models import FreezerItem, FreezerItemCreate

_store: dict[str, FreezerItem] = {}


def _new_id() -> str:
    return "itm_" + uuid.uuid4().hex[:8]


def create(data: FreezerItemCreate) -> FreezerItem:
    item = FreezerItem(id=_new_id(), **data.model_dump())
    _store[item.id] = item
    return item


def create_many(items: list[FreezerItemCreate]) -> list[FreezerItem]:
    return [create(i) for i in items]


def list_items() -> list[FreezerItem]:
    return list(_store.values())


def get(item_id: str) -> Optional[FreezerItem]:
    return _store.get(item_id)


def update(item_id: str, patch: dict) -> Optional[FreezerItem]:
    """Merge `patch` (already-validated, unset-excluded) and re-validate."""
    current = _store.get(item_id)
    if current is None:
        return None
    merged = {**current.model_dump(), **patch}
    item = FreezerItem(**merged)  # raises on invalid merged state
    _store[item_id] = item
    return item


def delete(item_id: str) -> bool:
    return _store.pop(item_id, None) is not None


def clear() -> None:
    """Test helper — reset the store."""
    _store.clear()
