"""User identity — real accounts when configured, per-browser demo otherwise.

The whole inventory layer is scoped by an opaque owner-id string (see
services/inventory.py). This module decides what that string is:

* **Accounts mode** — when ``SUPABASE_URL`` (or a legacy ``SUPABASE_JWT_SECRET``)
  is set, every protected request must carry a valid Supabase access token
  (``Authorization: Bearer <token>``). The owner id is the token's ``sub`` (the
  Supabase user id), so a freezer follows the *user* across every device they
  sign in on. Missing or invalid tokens get 401.

* **Demo mode** — when neither is set (local dev, the original public demo), this
  falls back to the legacy per-browser ``X-Client-Id`` behaviour, so nothing
  changes until accounts are switched on. The shared-password gate
  (security.require_access) still protects the routes in this mode.

Token signing: new Supabase projects sign access tokens with **asymmetric keys
(ES256)** and publish the public keys at a JWKS endpoint; older projects use a
shared **HS256** secret. We verify whichever the token declares — ES256/RS256 via
JWKS from ``SUPABASE_URL``, HS256 via ``SUPABASE_JWT_SECRET``. Supabase sets
``aud = "authenticated"``.
"""
from __future__ import annotations

import os
from typing import Optional

from fastapi import Header, HTTPException

_SUPABASE_AUDIENCE = "authenticated"
_ASYMMETRIC_ALGS = ("ES256", "ES384", "RS256")


def jwt_secret() -> Optional[str]:
    """Legacy HS256 shared secret (optional; only old projects need it)."""
    return os.environ.get("SUPABASE_JWT_SECRET")


def supabase_url() -> Optional[str]:
    """Project base URL, e.g. https://<ref>.supabase.co — used for JWKS."""
    url = os.environ.get("SUPABASE_URL")
    return url.rstrip("/") if url else None


def accounts_mode() -> bool:
    """True when real-account auth is configured (vs the per-browser demo)."""
    return bool(supabase_url() or jwt_secret())


def _bearer_token(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    parts = authorization.split(" ", 1)
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1].strip()
    return None


# JWKS client is created once and caches keys by `kid` (and refetches on a miss,
# so signing-key rotation is handled). Wrapped in _signing_key so tests can stub
# the network lookup.
_jwks_client = None


def _signing_key(token: str):
    """Return the public key that signed `token`, from the project JWKS."""
    global _jwks_client
    import jwt

    base = supabase_url()
    if not base:
        raise HTTPException(status_code=401, detail="token signed with an asymmetric key but SUPABASE_URL is not set")
    if _jwks_client is None:
        _jwks_client = jwt.PyJWKClient(f"{base}/auth/v1/.well-known/jwks.json")
    return _jwks_client.get_signing_key_from_jwt(token).key


def _verify_token(token: str) -> str:
    """Verify a Supabase access token and return its subject (user id)."""
    import jwt

    try:
        alg = jwt.get_unverified_header(token).get("alg", "")
        if alg in _ASYMMETRIC_ALGS:
            key = _signing_key(token)
            algorithms = list(_ASYMMETRIC_ALGS)
        elif alg == "HS256":
            key = jwt_secret()
            if not key:
                raise HTTPException(status_code=401, detail="HS256 token but SUPABASE_JWT_SECRET is not set")
            algorithms = ["HS256"]
        else:
            raise HTTPException(status_code=401, detail=f"unsupported token algorithm: {alg or 'none'}")

        payload = jwt.decode(
            token,
            key,
            algorithms=algorithms,
            audience=_SUPABASE_AUDIENCE,
            options={"require": ["exp", "sub"]},
        )
    except HTTPException:
        raise
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=401, detail=f"invalid token: {e}") from e

    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="token missing subject")
    return str(sub)


def get_owner_id(
    authorization: Optional[str] = Header(default=None),
    x_client_id: Optional[str] = Header(default=None),
) -> str:
    """Dependency returning the id that owns the request's inventory.

    Accounts mode: the authenticated Supabase user id (401 if not signed in).
    Demo mode: the per-browser client id (never blocks).
    """
    if accounts_mode():
        token = _bearer_token(authorization)
        if not token:
            raise HTTPException(status_code=401, detail="authentication required")
        return _verify_token(token)
    return (x_client_id or "").strip() or "shared"
