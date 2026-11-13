"""Photo parsing: unlabeled packs, logging of failures."""
from __future__ import annotations

import logging

from app.services import freezer_image


def test_prompt_covers_unlabeled_packs():
    t = freezer_image.PHOTO_INSTRUCTIONS
    assert "no writing" in t and '"pkgs"' in t and '"unknown"' in t and "Never invent weights" in t


def test_grouped_unknown_packs_come_back_flagged(monkeypatch):
    monkeypatch.setattr(freezer_image, "_vision_extract", lambda data, mime, hint=None: [
        {"species": "unknown", "cut": "steaks", "qty": 6, "unit": "pkgs"},
        {"species": "unknown", "cut": "roast", "qty": 3, "unit": "pkgs"},
        {"species": "unknown", "cut": "backstrap", "qty": 1, "unit": "pkgs"},
    ])
    cands = freezer_image.parse_image(b"jpeg", "image/jpeg")
    assert [(c.cut, c.qty, c.unit, c.species_unknown) for c in cands] == [
        ("steaks", 6, "pkgs", True), ("roast", 3, "pkgs", True), ("backstrap", 1, "pkgs", True)]


def test_note_names_the_animal_for_unlabeled_packs(monkeypatch):
    monkeypatch.setattr(freezer_image, "_vision_extract", lambda data, mime, hint=None: [
        {"species": "unknown", "cut": "steaks", "qty": 6, "unit": "pkgs"}])
    [c] = freezer_image.parse_image(b"jpeg", "image/jpeg", hint="elk")
    assert (c.species, c.category, c.species_unknown) == ("elk", "biggame", False)


def test_failures_are_logged_and_return_empty(monkeypatch, caplog):
    def boom(data, mime, hint=None):
        raise RuntimeError("openai said no")
    monkeypatch.setattr(freezer_image, "_vision_extract", boom)
    with caplog.at_level(logging.WARNING, logger=freezer_image.__name__):
        assert freezer_image.parse_image(b"x" * 10, "image/jpeg") == []
    msgs = [r.getMessage() for r in caplog.records]
    assert len(msgs) == 3 and all("openai said no" in m and "10 bytes" in m for m in msgs)
