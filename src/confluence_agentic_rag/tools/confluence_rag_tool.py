from typing import Dict, List, Optional
from .confluence_client import ConfluenceClient
from ..retrieval.chunking import html_to_text, chunk_text
from ..retrieval.rerank import rerank


def build_cql(space_key: Optional[str], query_hint: str) -> str:
    # Tuned for "decisions / ADRs / minutes"
    decision_terms = [
        "ADR",
        "Architecture Decision",
        "Decision",
        "Minutes",
        "Outcome",
        "Agentic AI",
        "Agentic AI Platform",
        query_hint,
    ]
    term_cql = " OR ".join([f'text ~ "{t}"' for t in decision_terms if t.strip()])
    cql = f"type=page AND ({term_cql})"
    if space_key:
        cql += f' AND space="{space_key}"'
    return cql


def confluence_decision_rag(
    client: ConfluenceClient,
    question: str,
    space_key: Optional[str] = None,
    limit_pages: int = 10,
    top_k_chunks: int = 8,
) -> Dict:
    cql = build_cql(space_key, query_hint="agentic platform")

    results = client.search_pages(cql, limit=limit_pages)

    chunks: List[Dict] = []
    for r in results:
        page = client.get_page(r["id"])
        title = page.get("title", "")
        url = client.page_url(page)
        html = page.get("body", {}).get("storage", {}).get("value", "")
        text = html_to_text(html)

        for ch in chunk_text(text):
            chunks.append(
                {
                    "page_id": r["id"],
                    "title": title,
                    "url": url,
                    "chunk": ch,
                }
            )

    top = rerank(question, chunks, top_k=top_k_chunks)

    context = "\n\n".join(
        [f"Source: {t['title']} ({t['url']})\nExcerpt: {t['chunk']}" for t in top]
    )

    return {"context": context, "sources": top, "cql": cql}
