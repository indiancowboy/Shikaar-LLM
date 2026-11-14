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
import logging
from typing import Optional

from ..config import GENERATION_MODEL, get_openai
from ..models import ParseCandidate
from .freezer_parse import (
    EXTRACTION_INSTRUCTIONS,
    EXTRACTION_SYSTEM,
    coerce_all,
)

log = logging.getLogger(__name__)

# Most real photos are a pile of vac-sealed packs with blank labels, not a cut
# sheet, so the model must describe what it sees when there's nothing to read.
PHOTO_INSTRUCTIONS = """
This photo shows freezer meat or fish. It may be a processor cut sheet, labeled
packages, or packages with no writing on them.

If there is writing (cut sheet, printed or handwritten labels), read it.

If packages have no readable writing, work PACKAGE BY PACKAGE. First list every
package you can see in "packages", then group them into "entries". Name each
package's cut from its shape through the plastic:
- backstrap / loin: a long, even, round log of muscle, often 8-20 inches
- tenderloin: small, thin and tapered, usually under 10 inches, often in pairs
- roast: a large, thick, irregular chunk or block (hindquarter, shoulder, neck)
- steaks: flat slices about 1/2-1.5 inches thick, often several per bag
- flank / flat cut: a thin, wide sheet of meat
- ground: a flat brick or slab with no visible grain or muscle shape
- stew meat: small cubes
- shank: round cross-section around a bone
- ribs: visible rib bones
- fillets / whole fish / whole bird / breasts for fish and birds
Never answer "unknown" or "mixed" for a cut you can see; give your best read.
Never invent weights: group same-cut packages into one entry with unit "pkgs"
and qty = how many packages.

Only name the animal if a label or the hunter's note says it; otherwise use
"species": "unknown".

JSON shape for photos:
{"packages": [{"n": 1, "looks_like": "long round log", "cut": "backstrap"}, ...],
 "entries": [{"species": ..., "category": ..., "cut": "backstrap", "qty": 1,
              "unit": "pkgs", "storage": "vacuum_sealed", "packs": null,
              "pack_size": null}, ...]}
"""


def _vision_extract(image_bytes: bytes, mime: str, hint: Optional[str] = None) -> list[dict]:
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
                        + "\n" + PHOTO_INSTRUCTIONS
                        + (f'\nNote from the hunter about this photo: "{hint}"' if hint else "")},
                    {"type": "image_url",
                     "image_url": {"url": f"data:{mime};base64,{b64}", "detail": "high"}},
                ],
            },
        ],
    )
    raw = (resp.choices[0].message.content or "").strip()
    data = json.loads(raw)
    entries = data.get("entries") or data.get("items") or _group_packages(data.get("packages"))
    if not isinstance(entries, list) or not entries:
        raise ValueError("no entries")
    return entries


def _group_packages(packages) -> list[dict]:
    """Fallback when the model lists packages but skips "entries": one entry
    per cut, qty = how many packages showed that cut."""
    counts: dict[str, int] = {}
    for pk in packages if isinstance(packages, list) else []:
        cut = str((pk or {}).get("cut") or "").strip().lower() if isinstance(pk, dict) else ""
        if cut:
            counts[cut] = counts.get(cut, 0) + 1
    return [{"species": "unknown", "cut": cut, "qty": n, "unit": "pkgs"} for cut, n in counts.items()]


def _ocr_fallback(image_bytes: bytes) -> Optional[list[dict]]:
    """Seam for the Tesseract OCR rung (brief §7 step 2). Disabled until the
    Tesseract dependency is approved; returns None so callers fall through to
    manual entry."""
    return None


def parse_image(
    image_bytes: bytes, mime: str = "image/jpeg", *, attempts: int = 3, hint: Optional[str] = None
) -> list[ParseCandidate]:
    """Vision extract -> (OCR seam) -> []. Never raises on model trouble."""
    raw: Optional[list[dict]] = None
    for attempt in range(1, attempts + 1):
        try:
            raw = _vision_extract(image_bytes, mime, hint)
            break
        except Exception as e:  # logged so Render's logs say why a photo failed
            log.warning("photo parse attempt %d/%d failed (%d bytes, %s): %r",
                        attempt, attempts, len(image_bytes), mime, e)
            raw = None

    offline = False
    if raw is None:
        raw = _ocr_fallback(image_bytes)  # currently disabled -> None
        offline = bool(raw)

    if not raw:
        return []
    return coerce_all(raw, offline=offline, hint=hint)
