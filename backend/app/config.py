"""Central configuration + shared service clients.

Single source of truth for the embedding/generation models and the Pinecone
index, so the ingestion scripts (ingest_recipes.py, ingest_cuisine.py) and the
API never drift apart. Clients are lazily created and cached so importing this
module never requires API keys (keeps unit tests offline-friendly).
"""
from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv

# Load backend/.env once on import.
load_dotenv()

# --- model + index identifiers (must match what the ingestion scripts used) ---
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536
GENERATION_MODEL = "gpt-4o"  # brief §1/§9; swappable
PINECONE_INDEX = "shikaar-recipes"


@lru_cache(maxsize=1)
def get_openai():
    """Return a cached OpenAI client. Imported lazily so this module has no
    hard dependency on the SDK being importable at collection time."""
    from openai import OpenAI

    return OpenAI(api_key=os.environ["OPENAI_API_KEY"])


@lru_cache(maxsize=1)
def get_pinecone_index():
    """Return a cached handle to the Pinecone recipe/cuisine index."""
    from pinecone import Pinecone

    pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
    return pc.Index(PINECONE_INDEX)
