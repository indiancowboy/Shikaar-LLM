"""/ask: answers from the library, and still answers if the index is down."""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.rag import generation, retrieval

client = TestClient(app)


def test_answers_with_sources(monkeypatch):
    monkeypatch.setattr(retrieval, "retrieve", lambda q, k, content_type=None: [
        {"id": "venison_curry", "score": 0.9, "metadata": {"title": "Venison Curry", "text": "sous vide 130F"}}])
    seen = {}
    monkeypatch.setattr(generation, "generate", lambda prompt, **kw: seen.setdefault("p", prompt) and "Cook it to 130°F.")
    body = client.post("/ask", json={"query": "how long to sous vide backstrap?"}).json()
    assert body["answer"] == "Cook it to 130°F."
    assert [s["title"] for s in body["sources"]] == ["Venison Curry"]
    assert "sous vide 130F" in seen["p"]


def test_still_answers_when_index_is_down(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("pinecone unreachable")
    monkeypatch.setattr(retrieval, "retrieve", boom)
    monkeypatch.setattr(generation, "generate", lambda prompt, **kw: "General advice.")
    body = client.post("/ask", json={"query": "best way to cook duck breast?"}).json()
    assert body == {"answer": "General advice.", "sources": []}


def test_model_failure_is_a_friendly_500_not_retried(monkeypatch):
    monkeypatch.setattr(retrieval, "retrieve", lambda *a, **k: [])
    def boom(prompt, **kw):
        raise RuntimeError("openai down")
    monkeypatch.setattr(generation, "generate", boom)
    r = client.post("/ask", json={"query": "anything"})
    assert r.status_code == 500 and "try again" in r.json()["detail"].lower()
