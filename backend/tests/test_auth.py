"""Tests for accounts mode (Supabase JWT auth).

Demo mode (no SUPABASE_JWT_SECRET) is covered by test_security.py and
test_freezer_api.py; here we turn accounts mode ON and check that a valid token
is required and that inventory is scoped to the token's user.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import inventory

client = TestClient(app)

SECRET = "test-jwt-secret"


@pytest.fixture(autouse=True)
def _accounts_mode(monkeypatch):
    """Enable accounts mode and ensure the password gate is off (as in prod)."""
    monkeypatch.setenv("SUPABASE_JWT_SECRET", SECRET)
    monkeypatch.delenv("SHIKAAR_ACCESS_PASSWORD", raising=False)
    inventory.clear()
    yield
    inventory.clear()


def _token(sub: str, *, expired: bool = False, aud: str = "authenticated") -> str:
    now = datetime.now(tz=timezone.utc)
    exp = now - timedelta(hours=1) if expired else now + timedelta(hours=1)
    return jwt.encode(
        {"sub": sub, "aud": aud, "exp": exp, "iat": now}, SECRET, algorithm="HS256"
    )


def _bearer(sub: str, **kw) -> dict:
    return {"Authorization": f"Bearer {_token(sub, **kw)}"}


def _item(**over) -> dict:
    base = dict(
        species="whitetail", category="biggame", cut="backstrap", qty=2,
        unit="lbs", storage="vacuum_sealed",
        date_frozen=str(date.today() - timedelta(days=10)),
    )
    base.update(over)
    return base


def test_requires_token():
    assert client.get("/freezer").status_code == 401
    assert client.get("/fish").status_code == 401


def test_rejects_bad_tokens():
    assert client.get("/freezer", headers={"Authorization": "Bearer nonsense"}).status_code == 401
    assert client.get("/freezer", headers=_bearer("u1", expired=True)).status_code == 401
    assert client.get("/freezer", headers=_bearer("u1", aud="wrong")).status_code == 401


def test_inventory_scoped_to_user():
    alice = _bearer("user-alice")
    bob = _bearer("user-bob")

    client.post("/freezer", json=_item(), headers=alice)
    assert len(client.get("/freezer", headers=alice).json()) == 1
    assert client.get("/freezer", headers=bob).json() == []  # bob can't see alice's

    aid = client.get("/freezer", headers=alice).json()[0]["id"]
    assert client.delete(f"/freezer/{aid}", headers=bob).status_code == 404  # nor touch it
    assert client.delete(f"/freezer/{aid}", headers=alice).status_code == 204


def test_same_user_different_token_same_freezer():
    """A freezer follows the user id, not the token/device."""
    client.post("/freezer", json=_item(), headers=_bearer("user-alice"))
    # A fresh token for the same subject (e.g. signing in on another device).
    assert len(client.get("/freezer", headers=_bearer("user-alice")).json()) == 1


# --------------------------------------------------------------- ES256 path ---
# New Supabase projects sign tokens with asymmetric ES256 keys verified via JWKS.
# We generate a real EC keypair, mint ES256 tokens, and stub the JWKS lookup so
# the verification runs offline (no network to Supabase).

from app import auth  # noqa: E402


@pytest.fixture()
def es256(monkeypatch):
    from cryptography.hazmat.primitives.asymmetric import ec

    # Accounts mode via SUPABASE_URL only (no shared secret) — Nikhil's real setup.
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.delenv("SUPABASE_JWT_SECRET", raising=False)

    priv = ec.generate_private_key(ec.SECP256R1())
    monkeypatch.setattr(auth, "_signing_key", lambda _token: priv.public_key())
    inventory.clear()
    yield priv
    inventory.clear()


def _es_token(priv, sub: str, **over) -> str:
    from datetime import datetime, timedelta, timezone

    now = datetime.now(tz=timezone.utc)
    claims = {
        "sub": sub, "aud": "authenticated", "iat": now,
        "exp": now + timedelta(hours=1),
    }
    claims.update(over)
    return jwt.encode(claims, priv, algorithm="ES256", headers={"kid": "key-1"})


def _es_bearer(priv, sub: str, **over) -> dict:
    return {"Authorization": f"Bearer {_es_token(priv, sub, **over)}"}


def test_es256_requires_token(es256):
    assert client.get("/freezer").status_code == 401


def test_es256_valid_token_and_scoping(es256):
    priv = es256
    client.post("/freezer", json=_item(), headers=_es_bearer(priv, "alice"))
    assert len(client.get("/freezer", headers=_es_bearer(priv, "alice")).json()) == 1
    assert client.get("/freezer", headers=_es_bearer(priv, "bob")).json() == []


def test_es256_rejects_expired(es256):
    from datetime import datetime, timedelta, timezone

    past = datetime.now(tz=timezone.utc) - timedelta(hours=1)
    assert client.get(
        "/freezer", headers=_es_bearer(es256, "alice", exp=past)
    ).status_code == 401


def test_es256_rejects_wrong_audience(es256):
    assert client.get(
        "/freezer", headers=_es_bearer(es256, "alice", aud="wrong")
    ).status_code == 401
