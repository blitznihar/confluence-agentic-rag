from __future__ import annotations

from typing import Dict, List, Optional
from sentence_transformers import SentenceTransformer

from confluence_agentic_rag.tools.confluence_client import ConfluenceClient
from confluence_agentic_rag.retrieval.chunking import html_to_text, chunk_text
from vectorstore.schema import ensure_schema
from vectorstore.weaviate_store import WeaviateStore

_embed_model = SentenceTransformer("all-MiniLM-L6-v2")


def ingest_space_decisions(
    confluence: ConfluenceClient,
    store: WeaviateStore,
    space_key: Optional[str] = None,
    limit_pages: int = 50,
) -> Dict[str, int]:
    """
    Pulls pages likely to contain ADRs/decisions 
    and indexes them into Weaviate.
    """
    ensure_schema(store.client)

    terms = ["ADR",
             "Decision",
             "Minutes",
             "Architecture Decision",
             "Agentic AI",
             "Agentic AI Platform"]
    term_cql = " OR ".join([f'text ~ "{t}"' for t in terms])
    cql = f'type=page AND ({term_cql})'
    if space_key:
        cql += f' AND space="{space_key}"'

    results = confluence.search_pages(cql, limit=limit_pages)

    to_upsert: List[Dict] = []
    pages = 0
    chunks = 0

    for r in results:
        page = confluence.get_page(r["id"])
        pages += 1

        title = page.get("title", "")
        url = confluence.page_url(page)
        html = page.get("body", {}).get("storage", {}).get("value", "")
        text = html_to_text(html)
        version_num = int(page.get("version", {}).get("number", 0) or 0)
        space = page.get("space", {}).get("key", "") or (space_key or "")

        chs = chunk_text(text)
        if not chs:
            continue

        vecs = _embed_model.encode(chs, normalize_embeddings=True)

        for chunk_text_i, vec in zip(chs, vecs):
            to_upsert.append({
                "properties": {
                    "page_id": r["id"],
                    "title": title,
                    "url": url,
                    "chunk": chunk_text_i,
                    "space_key": space,
                    "version": version_num,
                },
                "vector": vec.tolist(),
            })
            chunks += 1

    store.upsert_chunks(to_upsert)
    return {"pages_indexed": pages, "chunks_indexed": chunks}
