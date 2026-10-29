"""Daily AI-action limit per user."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import freezer_parse, usage

client = TestClient(app)


@pytest.fixture(autouse=True)
def _limit_of_three(monkeypatch):
    monkeypatch.setenv("AI_DAILY_LIMIT", "3")
    # no network: the parser falls back offline immediately
    monkeypatch.setattr(freezer_parse, "_llm_extract", lambda t: (_ for _ in ()).throw(RuntimeError("down")))
    usage.reset()
    yield
    usage.reset()


def _parse(client_id: str):
    return client.post("/freezer/parse", json={"text": "2 elk backstraps"}, headers={"X-Client-Id": client_id})


def test_blocks_after_the_daily_limit():
    assert [(_parse("alice").status_code) for _ in range(3)] == [200, 200, 200]
    r = _parse("alice")
    assert r.status_code == 429
    assert "3 AI actions" in r.json()["detail"]


def test_limit_is_per_user():
    for _ in range(4):
        _parse("alice")
    assert _parse("bob").status_code == 200


def test_resets_the_next_day(monkeypatch):
    monkeypatch.setattr(usage, "_today", lambda: "2026-01-01")
    for _ in range(3):
        _parse("alice")
    assert _parse("alice").status_code == 429
    monkeypatch.setattr(usage, "_today", lambda: "2026-01-02")
    assert _parse("alice").status_code == 200


def test_all_ai_routes_share_the_count():
    h = {"X-Client-Id": "carol"}
    assert client.post("/freezer/meal-plan", json={}, headers=h).status_code == 200   # empty freezer, no model call
    assert _parse("carol").status_code == 200
    r = client.post("/freezer/parse-image", files={"file": ("x.jpg", b"img", "image/jpeg")}, headers=h)
    assert r.status_code == 200
    assert client.post("/freezer/meal-plan", json={}, headers=h).status_code == 429


def test_non_ai_routes_are_unlimited():
    for _ in range(5):
        _parse("dave")
    h = {"X-Client-Id": "dave"}
    assert client.post("/freezer/estimate-yield", json={"species": "elk", "weight": 500}, headers=h).status_code == 200
    assert client.get("/freezer", headers=h).status_code == 200
    assert client.get("/freezer/cook-first", headers=h).status_code == 200


def test_zero_turns_the_limit_off(monkeypatch):
    monkeypatch.setenv("AI_DAILY_LIMIT", "0")
    assert all(_parse("erin").status_code == 200 for _ in range(6))


def test_bad_env_value_falls_back_to_default(monkeypatch):
    monkeypatch.setenv("AI_DAILY_LIMIT", "lots")
    assert usage.daily_limit() == usage.DEFAULT_LIMIT
