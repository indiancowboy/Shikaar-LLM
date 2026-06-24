"""Tests for the shared-password access gate."""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
PW = {"X-Access-Password": "secret123"}


def test_gate_disabled_when_env_unset(monkeypatch):
    monkeypatch.delenv("SHIKAAR_ACCESS_PASSWORD", raising=False)
    assert client.get("/auth/check").json() == {"ok": True}
    assert client.get("/fish").status_code == 200


def test_gate_blocks_without_password(monkeypatch):
    monkeypatch.setenv("SHIKAAR_ACCESS_PASSWORD", "secret123")
    assert client.get("/fish").status_code == 401
    assert client.get("/auth/check").status_code == 401


def test_gate_allows_with_correct_password(monkeypatch):
    monkeypatch.setenv("SHIKAAR_ACCESS_PASSWORD", "secret123")
    assert client.get("/auth/check", headers=PW).json() == {"ok": True}
    assert client.get("/fish", headers=PW).status_code == 200
    assert client.get("/fish", headers={"X-Access-Password": "wrong"}).status_code == 401


def test_health_open_even_when_gated(monkeypatch):
    monkeypatch.setenv("SHIKAAR_ACCESS_PASSWORD", "secret123")
    assert client.get("/health").status_code == 200
