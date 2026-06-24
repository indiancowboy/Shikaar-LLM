"""Shikaar FastAPI app.

Phase 0 surface: a health check and a working end-to-end "Ask Shikaar" RAG
endpoint (embed query -> Pinecone retrieve -> GPT-4o generate). Freezer Hub
endpoints (brief §10) are added in Phase 1 on top of this same RAG layer.
"""
from __future__ import annotations

from typing import Optional

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from .rag import generation, retrieval
from .routers import fish, freezer
from .security import require_access

app = FastAPI(title="Shikaar API", version="0.1.0")

# CORS — wide-open (the password gate is what protects the API, not the origin).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Expensive routes sit behind the shared-password gate (no-op when unset locally).
app.include_router(freezer.router, dependencies=[Depends(require_access)])
app.include_router(fish.router, dependencies=[Depends(require_access)])


@app.get("/", include_in_schema=False)
def root():
    """The bare root has no API; send curious browsers to the docs."""
    return RedirectResponse(url="/docs")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/auth/check", dependencies=[Depends(require_access)])
def auth_check() -> dict:
    """Returns ok if the access password is valid (or the gate is disabled).
    The frontend calls this to validate a password before storing it."""
    return {"ok": True}


class AskRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)
    content_type: Optional[str] = None  # "recipe" | "cuisine" | None (both)


class Source(BaseModel):
    id: str
    title: str
    score: float


class AskResponse(BaseModel):
    answer: str
    sources: list[Source]


@app.post("/ask", response_model=AskResponse, dependencies=[Depends(require_access)])
def ask(req: AskRequest) -> AskResponse:
    """General RAG Q&A over the recipe/cuisine knowledge base."""
    matches = retrieval.retrieve(req.query, req.top_k, content_type=req.content_type)
    context = retrieval.format_context(matches)
    prompt = (
        "Answer the user's question using the retrieved knowledge base entries "
        "below. Stay grounded in them; if they don't cover it, say so and give "
        "your best wild-game cooking guidance.\n\n"
        f"# Retrieved knowledge base\n{context}\n\n"
        f"# Question\n{req.query}"
    )
    answer = generation.generate(prompt)
    sources = [
        Source(
            id=m["id"],
            title=m["metadata"].get("title", "Untitled"),
            score=m["score"],
        )
        for m in matches
    ]
    return AskResponse(answer=answer, sources=sources)
