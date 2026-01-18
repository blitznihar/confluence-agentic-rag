"""
RAG Orchestrator.

- Embeds the user question
- Retrieves top-k semantically similar Confluence chunks from Weaviate
- Builds a grounded prompt with citations
- Calls the configured LLM (StubLLM for now)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from sentence_transformers import SentenceTransformer


_EMBED_MODEL: Optional[SentenceTransformer] = None


def _embed(text: str) -> List[float]:
    global _EMBED_MODEL  # pylint: disable=global-statement
    if _EMBED_MODEL is None:
        # Good default; keep consistent with your ingestion embeddings
        _EMBED_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    vec = _EMBED_MODEL.encode(text, normalize_embeddings=True)
    return vec.tolist()


def _normalize_url(url: str) -> str:
    """Fix Confluence URL if it was double-prefixed during older ingests."""
    prefix = "https://blitznihar.atlassian.net/"
    double = prefix + "https://blitznihar.atlassian.net/"
    if url.startswith(double):
        return url[len(prefix) :]
    return url


def _dedupe_hits(hits: list[dict]) -> list[dict]:
    """
    Remove duplicate retrieval hits and normalize URLs so ALL outputs are clean
    (prompt + Top Sources).
    """
    out: list[dict] = []
    seen: set[tuple[str, str]] = set()

    for h in hits:
        # normalize URL and persist it back into the hit
        url = _normalize_url((h.get("url", "") or "").strip())
        h["url"] = url

        chunk = (h.get("chunk", "") or "").strip()
        key = (url, chunk)

        if key in seen:
            continue

        seen.add(key)
        out.append(h)

    return out


def _build_prompt(question: str, hits: List[Dict[str, Any]]) -> str:
    header = (
        "You are an enterprise architecture assistant.\n"
        "Answer using ONLY the provided Confluence excerpts.\n"
        'If insufficient, say: "I don\'t have enough information in Confluence."\n'
        "Add citations as (URL) at the end of sentences.\n\n"
        f"Question:\n{question}\n\n"
        "Confluence Excerpts:\n"
    )

    chunks = []
    for h in hits:
        title = h.get("title", "Untitled")
        url = _normalize_url(h.get("url", "") or "")
        excerpt = (h.get("chunk", "") or "").strip().replace("\n", " ")
        excerpt = excerpt[:1200]  # keep prompt size reasonable
        chunks.append(f"Source: {title}\n({url})\nExcerpt: {excerpt}\n")

    return header + "\n".join(chunks)


def answer(
    question: str,
    store: Any,
    llm: Any,
    space_key: Optional[str] = None,
    top_k: int = 8,
) -> Dict[str, Any]:
    """Answer a question using vector retrieval + grounded generation."""
    qv = _embed(question)

    hits = store.semantic_search(
        query_vector=qv,
        top_k=top_k,
        where_filter={"space_key": space_key} if space_key else None,
    )
    hits = _dedupe_hits(hits)

    # If nothing retrieved, return grounded "no info"
    if not hits:
        return {"answer": "I don't have enough information in Confluence.", "sources": []}

    prompt = _build_prompt(question, hits)
    resp = llm.generate(prompt)

    return {"answer": resp, "sources": hits}
