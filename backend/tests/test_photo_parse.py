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


# ------------------------------------------------- package-by-package reads ---
import json as _json
from types import SimpleNamespace


def _fake_openai(monkeypatch, reply: dict):
    sent = {}

    def create(**kw):
        sent.update(kw)
        msg = SimpleNamespace(content=_json.dumps(reply))
        return SimpleNamespace(choices=[SimpleNamespace(message=msg)])

    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    monkeypatch.setattr(freezer_image, "get_openai", lambda: client)
    return sent


def test_prompt_has_cut_guide_and_asks_package_by_package():
    t = freezer_image.PHOTO_INSTRUCTIONS
    for word in ("backstrap", "tenderloin", "roast", "steaks", "ground", "PACKAGE BY PACKAGE", '"packages"'):
        assert word in t
    assert 'Never answer "unknown"' in t


def test_request_uses_high_detail(monkeypatch):
    sent = _fake_openai(monkeypatch, {"entries": [{"species": "unknown", "cut": "roast", "qty": 2, "unit": "pkgs"}]})
    freezer_image.parse_image(b"jpeg", "image/jpeg")
    image_part = sent["messages"][1]["content"][1]
    assert image_part["image_url"]["detail"] == "high"


def test_packages_only_reply_is_grouped_by_cut(monkeypatch):
    _fake_openai(monkeypatch, {"packages": [
        {"n": 1, "looks_like": "long round log", "cut": "backstrap"},
        {"n": 2, "looks_like": "big chunk", "cut": "roast"},
        {"n": 3, "looks_like": "big chunk", "cut": "roast"},
        {"n": 4, "looks_like": "flat slices", "cut": "steaks"},
        {"n": 5, "looks_like": "flat slices", "cut": "Steaks"},
        {"n": 6, "looks_like": "flat slices", "cut": "steaks"},
    ]})
    cands = freezer_image.parse_image(b"jpeg", "image/jpeg", hint="mule deer")
    got = {(c.cut, c.qty, c.unit, c.species) for c in cands}
    assert got == {("backstrap", 1, "pkgs", "mule_deer"), ("roast", 2, "pkgs", "mule_deer"),
                   ("steaks", 3, "pkgs", "mule_deer")}
