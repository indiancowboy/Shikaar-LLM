"""Light shared-password gate for public demo deploys.

Protects the expensive routes (/ask, /freezer/*, /fish/*) so a public URL can't
burn OpenAI/Pinecone credits. The password is set via the SHIKAAR_ACCESS_PASSWORD
env var on the host; the frontend sends it as the `X-Access-Password` header
(typed by the user, never baked into the public bundle).

If SHIKAAR_ACCESS_PASSWORD is unset (local dev), the gate is a no-op — zero
friction. This is a speed bump for a small demo, not real auth.
"""
from __future__ import annotations

import os
from typing import Optional

from fastapi import Header, HTTPException


def require_access(x_access_password: Optional[str] = Header(default=None)) -> None:
    expected = os.environ.get("SHIKAAR_ACCESS_PASSWORD")
    if not expected:
        return  # gate disabled
    if x_access_password != expected:
        raise HTTPException(status_code=401, detail="invalid or missing access password")
