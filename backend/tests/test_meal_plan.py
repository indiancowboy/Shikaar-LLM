"""Meal planner: shortlist, validation, retry — model and vector index stubbed."""
from __future__ import annotations

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import FreezerItem
from app.rag import generation, retrieval
from app.services import cook_first, inventory, meal_plan

client = TestClient(app)

GROUND = FreezerItem(id="itm_g", species="wild_hog", category="hog", cut="ground", qty=1, unit="lbs",
                     storage="vacuum_sealed", date_frozen=date.today() - timedelta(days=20),
                     packs=10, pack_size=2)

CREATIVE = {
    "title": "Chettinad Boar Kebabs", "kind": "creative", "recipe_id": None,
    "cuisine": "Tamil Nadu", "uses": [{"item_id": "itm_g", "packs": 1}],
    "why": "Ground boar holds a kebab shape.", "adaptation": None,
    "time": "35 min", "serves": 4,
    "ingredients": ["2 lb ground wild boar", "1 tbsp black pepper", "1 onion, grated"],
    "steps": ["Mix and shape.", "Grill to 160°F."],
}


@pytest.fixture(autouse=True)
def _stub_index(monkeypatch):
    monkeypatch.setattr(retrieval, "retrieve", lambda *a, **k: [])


def _stub_model(monkeypatch, *responses):
    calls = {"prompts": []}
    seq = list(responses)

    def fake(prompt, **kw):
        calls["prompts"].append(prompt)
        r = seq.pop(0) if seq else {"meals": []}
        if isinstance(r, Exception):
            raise r
        return r

    monkeypatch.setattr(generation, "generate_json", fake)
    return calls


def test_prompt_only_offers_recipes_that_fit(monkeypatch):
    calls = _stub_model(monkeypatch, {"meals": [CREATIVE]})
    meal_plan.meal_plan([GROUND])
    p = calls["prompts"][0]
    assert "butter_keema" in p and "wild_boar_breakfast_pizza" in p
    assert "Season the ground meat into sausage" in p      # adapt note shown
    assert "cambodianstyle_deer_tenderloin" not in p and "venison_curry" not in p
    assert "10 packs × 2 lbs (20 lbs)" in p


def test_library_meal_gets_verbatim_recipe_and_server_adaptation(monkeypatch):
    _stub_model(monkeypatch, {"meals": [
        {"title": "Breakfast Pizza", "kind": "library", "recipe_id": "wild_boar_breakfast_pizza",
         "uses": [{"item_id": "itm_g", "packs": 1}], "why": "Brunch.", "adaptation": None},
        CREATIVE,
    ]})
    out = meal_plan.meal_plan([GROUND])
    pizza = out["meals"][0]
    assert pizza["kind"] == "library"
    assert pizza["recipe"]["title"] == "Wild Boar Breakfast Pizza"
    assert "Preheat oven" in pizza["recipe"]["text"]
    assert "sausage" in pizza["adaptation"].lower()        # filled from the matcher
    assert out["meals"][1]["kind"] == "creative" and out["meals"][1]["steps"]


def test_invalid_meals_are_dropped(monkeypatch):
    _stub_model(monkeypatch, {"meals": [
        # recipe that doesn't fit ground meat
        {"title": "Tenderloin", "kind": "library", "recipe_id": "cambodianstyle_deer_tenderloin",
         "uses": [{"item_id": "itm_g"}]},
        # made-up recipe id
        {"title": "Mystery", "kind": "library", "recipe_id": "nope", "uses": [{"item_id": "itm_g"}]},
        # item not in the freezer
        {**CREATIVE, "title": "Ghost", "uses": [{"item_id": "itm_missing"}]},
        # creative without a real recipe
        {**CREATIVE, "title": "Vague", "ingredients": ["boar"], "steps": []},
        # duplicate title
        CREATIVE, CREATIVE,
    ]})
    out = meal_plan.meal_plan([GROUND])
    assert [m["title"] for m in out["meals"]] == ["Chettinad Boar Kebabs"]


def test_packs_are_clamped_to_what_the_item_has(monkeypatch):
    _stub_model(monkeypatch, {"meals": [{**CREATIVE, "uses": [{"item_id": "itm_g", "packs": 99}]}]})
    assert meal_plan.meal_plan([GROUND])["meals"][0]["uses"] == [{"item_id": "itm_g", "packs": 10}]


def test_retries_once_after_bad_output(monkeypatch):
    calls = _stub_model(monkeypatch, ValueError("bad json"), {"meals": [CREATIVE]})
    out = meal_plan.meal_plan([GROUND])
    assert len(calls["prompts"]) == 2 and out["meals"]


def test_gives_up_calmly(monkeypatch):
    _stub_model(monkeypatch, {"meals": []}, {"meals": []})
    out = meal_plan.meal_plan([GROUND])
    assert out["meals"] == [] and "try again" in out["plan"]


def test_works_when_vector_index_is_down(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("pinecone down")
    monkeypatch.setattr(retrieval, "retrieve", boom)
    _stub_model(monkeypatch, {"meals": [CREATIVE]})
    assert meal_plan.meal_plan([GROUND])["meals"]


def test_meal_plan_endpoint(monkeypatch):
    inventory.clear()
    iid = client.post("/freezer", json={
        "species": "wild_hog", "category": "hog", "cut": "ground", "qty": 1, "unit": "lbs",
        "storage": "vacuum_sealed", "date_frozen": str(date.today()), "packs": 10, "pack_size": 2,
    }).json()["id"]
    _stub_model(monkeypatch, {"meals": [{**CREATIVE, "uses": [{"item_id": iid, "packs": 1}]}]})
    body = client.post("/freezer/meal-plan", json={}).json()
    assert body["meals"][0]["uses"] == [{"item_id": iid, "packs": 1}]
    assert "Chettinad Boar Kebabs" in body["plan"]
    inventory.clear()


def test_cook_first_suggests_matching_recipes():
    old = GROUND.model_copy(update={"date_frozen": date.today() - timedelta(days=900)})
    out = cook_first.cook_first([old])
    assert out["urgent"]
    titles = out["cards"][0]["suggestions"]
    assert titles and "Cambodian-Style Deer Tenderloin" not in titles
    assert all(t in {"Butter Keema", "Desi Deer Flatbread", "Keema (Ground Meat)", "Keema Kachori",
                     "Wild Boar Mirchi Bajji", "Wild Boar Breakfast Pizza"} for t in titles)
