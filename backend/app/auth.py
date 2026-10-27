"""User identity — real accounts when configured, per-browser demo otherwise.

The whole inventory layer is scoped by an opaque owner-id string (see
services/inventory.py). This module decides what that string is:

* **Accounts mode** — when ``SUPABASE_JWT_SECRET`` is set, every protected
  request must carry a valid Supabase JWT (``Authorization: Bearer <token>``).
  The owner id is the token's ``sub`` (the Supabase user id), so a freezer
  follows the *user* across every device they sign in on. Missing or invalid
  tokens get 401.

* **Demo mode** — when the secret is unset (local dev, current public demo),
  this falls back to the legacy per-browser ``X-Client-Id`` behaviour, so
  nothing changes until accounts are switched on. The shared-password gate
  (security.require_access) still protects the routes in this mode.

Supabase signs access tokens HS256 with the project's JWT secret (Project
Settings -> API -> JWT Settings) and sets ``aud = "authenticated"``.
"""
from __future__ import annotations

import os
from typing import Optional

from fastapi import Header, HTTPException

_SUPABASE_AUDIENCE = "authenticated"


def jwt_secret() -> Optional[str]:
    return os.environ.get("SUPABASE_JWT_SECRET")


def accounts_mode() -> bool:
    """True when real-account auth is configured (vs the per-browser demo)."""
    return bool(jwt_secret())


def _bearer_token(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    parts = authorization.split(" ", 1)
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1].strip()
    return None


def _verify_supabase_jwt(token: str) -> str:
    """Verify a Supabase access token and return its subject (user id)."""
    import jwt  # PyJWT — imported lazily so demo mode needs no crypto deps

    try:
        payload = jwt.decode(
            token,
            jwt_secret(),
            algorithms=["HS256"],
            audience=_SUPABASE_AUDIENCE,
            options={"require": ["exp", "sub"]},
        )
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
        return _verify_supabase_jwt(token)
    return (x_client_id or "").strip() or "shared"
