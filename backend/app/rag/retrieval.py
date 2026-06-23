"""Core RAG retrieval — embed a query and search the recipe/cuisine index.

The single shared retrieval path. Cook First and the meal planner bias results
by querying with species/cut context; this module stays generic.
"""
from __future__ import annotations

from typing import Optional

from ..config import EMBEDDING_MODEL, get_openai, get_pinecone_index


def embed(text: str) -> list[float]:
    """Embed text with the same model the ingestion scripts used."""
    resp = get_openai().embeddings.create(model=EMBEDDING_MODEL, input=text)
    return resp.data[0].embedding


def retrieve(
    query: str,
    top_k: int = 5,
    *,
    content_type: Optional[str] = None,
) -> list[dict]:
    """Embed `query` and return the top_k matching KB chunks.

    Args:
        query: natural-language query.
        top_k: number of matches to return.
        content_type: optional metadata filter ("recipe" or "cuisine").

    Returns:
        A list of {id, score, metadata} dicts, highest score first.
    """
    vector = embed(query)
    flt = {"content_type": {"$eq": content_type}} if content_type else None
    res = get_pinecone_index().query(
        vector=vector,
        top_k=top_k,
        include_metadata=True,
        filter=flt,
    )
    return [
        {"id": m["id"], "score": m["score"], "metadata": m.get("metadata", {})}
        for m in res.get("matches", [])
    ]


def format_context(matches: list[dict]) -> str:
    """Render retrieved matches into a context block for generation."""
    blocks = []
    for m in matches:
        md = m["metadata"]
        title = md.get("title", "Untitled")
        text = md.get("text", "")
        blocks.append(f"## {title}\n{text}")
    return "\n\n".join(blocks)
