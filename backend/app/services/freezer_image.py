"""Image logging (build brief §7) — photo of a cut sheet / labels -> candidates.

Same downstream pipeline as freezer_parse: GPT-4o is multimodal, so we send the
image with the same JSON contract, then validate/confirm identically.

Degradation: (1) vision extract, retry up to 3x. (2) OCR fallback (Tesseract) ->
keyword parser. (3) manual entry.

NOTE: the Tesseract OCR rung (step 2) is intentionally NOT wired up — Tesseract
is a new system dependency and the brief says to confirm before adding one. For
now an unreadable image returns [] and the UI routes the user to manual entry.
See `_ocr_fallback` below for the seam.
"""
from __future__ import annotations

import base64
from typing import Optional

from ..config import GENERATION_MODEL, get_openai
from ..models import ParseCandidate
from .freezer_parse import (
    EXTRACTION_INSTRUCTIONS,
    EXTRACTION_SYSTEM,
    coerce_all,
)


def _vision_extract(image_bytes: bytes, mime: str) -> list[dict]:
    """One multimodal model attempt. Returns raw entry dicts or raises."""
    import json

    b64 = base64.b64encode(image_bytes).decode("ascii")
    resp = get_openai().chat.completions.create(
        model=GENERATION_MODEL,
        max_tokens=1500,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": EXTRACTION_SYSTEM},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": EXTRACTION_INSTRUCTIONS
                        + "\n\nRead every item from this processor cut sheet / package labels."},
                    {"type": "image_url",
                     "image_url": {"url": f"data:{mime};base64,{b64}"}},
                ],
            },
        ],
    )
    raw = (resp.choices[0].message.content or "").strip()
    data = json.loads(raw)
    entries = data.get("entries") or data.get("items") or []
    if not isinstance(entries, list) or not entries:
        raise ValueError("no entries")
    return entries


def _ocr_fallback(image_bytes: bytes) -> Optional[list[dict]]:
    """Seam for the Tesseract OCR rung (brief §7 step 2). Disabled until the
    Tesseract dependency is approved; returns None so callers fall through to
    manual entry."""
    return None


def parse_image(image_bytes: bytes, mime: str = "image/jpeg", *, attempts: int = 3) -> list[ParseCandidate]:
    """Vision extract -> (OCR seam) -> []. Never raises on model trouble."""
    raw: Optional[list[dict]] = None
    for _ in range(attempts):
        try:
            raw = _vision_extract(image_bytes, mime)
            break
        except Exception:
            raw = None

    offline = False
    if raw is None:
        raw = _ocr_fallback(image_bytes)  # currently disabled -> None
        offline = bool(raw)

    if not raw:
        return []
    return coerce_all(raw, offline=offline)
