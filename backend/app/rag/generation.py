"""Generation wrapper — GPT-4o in the Two Brown Guys Hunt (TBGH) voice.

Kept server-side: the browser never holds a model key (the prototype's direct
api calls were a demo harness only). The meal planner passes its own task
instructions as the user prompt; this module owns the persona + the call.
"""
from __future__ import annotations

from ..config import GENERATION_MODEL, get_openai

TBGH_SYSTEM = (
    "You are Shikaar, the cooking assistant for the YouTube channel "
    '"Two Brown Guys Hunt" (TBGH). You specialize in wild game and fish — '
    "venison, wild boar, elk, waterfowl, bear, and both lean and oily fish — "
    "with a confident Indian/South-Asian spice-fusion lean. Voice: warm, "
    "direct, like an experienced hunting buddy who actually cooks. Be concrete "
    "and encouraging. No preamble, no hedging disclaimers."
)


def generate(
    prompt: str,
    *,
    system: str = TBGH_SYSTEM,
    max_tokens: int = 1000,
    temperature: float = 0.7,
) -> str:
    """Generate a completion in the TBGH voice and return its text."""
    resp = get_openai().chat.completions.create(
        model=GENERATION_MODEL,
        max_tokens=max_tokens,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
    )
    return (resp.choices[0].message.content or "").strip()
