"""Unknown animals are flagged (never guessed), and a photo note fills them in."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.domain.parsing import fallback_parse
from app.main import app
from app.services import freezer_image, freezer_parse

client = TestClient(app)

RAW_NO_ANIMAL = [
    {"species": "unknown", "category": "biggame", "cut": "backstrap", "qty": 2, "unit": "pkgs"},
    {"species": "", "cut": "ground", "qty": 8, "unit": "lbs"},
]


def test_unknown_species_is_flagged_not_guessed():
    a, b = freezer_parse.coerce_all(RAW_NO_ANIMAL, offline=False)
    assert a.species == "unknown" and a.species_unknown
    assert b.species == "unknown" and b.species_unknown   # empty species kept, not dropped
    assert b.packs == 8                                    # 1 lb packs still apply


def test_hint_fills_unknown_species():
    a, b = freezer_parse.coerce_all(RAW_NO_ANIMAL, offline=False, hint="wild hog")
    assert (a.species, a.category, a.species_unknown) == ("wild_hog", "hog", False)
    assert (b.species, b.category, b.species_unknown) == ("wild_hog", "hog", False)


def test_hint_does_not_override_a_named_animal():
    [c] = freezer_parse.coerce_all(
        [{"species": "elk", "category": "biggame", "cut": "steaks", "qty": 3, "unit": "lbs"}],
        offline=False, hint="wild hog")
    assert c.species == "elk" and not c.species_unknown


def test_unrecognised_hint_leaves_entry_flagged():
    [c, _] = freezer_parse.coerce_all(RAW_NO_ANIMAL, offline=False, hint="the good stuff")
    assert c.species_unknown


def test_fallback_parse_without_animal_returns_unknown_cuts():
    res = fallback_parse("2 backstraps and 8 lbs ground")
    assert {c["cut"] for c in res} == {"backstrap", "ground"}
    assert all(c["species"] == "unknown" for c in res)
    assert fallback_parse("put some random stuff in the freezer") == []


def test_parse_text_endpoint_flags_unknown(monkeypatch):
    monkeypatch.setattr(freezer_parse, "_llm_extract", lambda t: (_ for _ in ()).throw(RuntimeError("down")))
    d = client.post("/freezer/parse", json={"text": "2 backstraps and 8 lbs ground"}).json()
    assert d["candidates"] and all(c["species_unknown"] for c in d["candidates"])


@pytest.mark.parametrize("hint,expected", [("wild hog", ("wild_hog", False)), (None, ("unknown", True))])
def test_parse_image_endpoint_uses_hint(monkeypatch, hint, expected):
    seen = {}

    def fake_vision(data, mime, h=None):
        seen["hint"] = h
        return [{"species": "unknown", "cut": "shoulder roast", "qty": 3, "unit": "lbs"}]

    monkeypatch.setattr(freezer_image, "_vision_extract", fake_vision)
    form = {"hint": hint} if hint else {}
    d = client.post("/freezer/parse-image", files={"file": ("sheet.jpg", b"fakejpeg", "image/jpeg")}, data=form).json()
    c = d["candidates"][0]
    assert (c["species"], c["species_unknown"]) == expected
    assert seen["hint"] == hint


def test_prompt_tells_model_not_to_guess():
    assert '"unknown"' in freezer_parse.EXTRACTION_INSTRUCTIONS
