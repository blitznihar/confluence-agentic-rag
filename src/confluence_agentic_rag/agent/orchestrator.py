from typing import Optional, Dict
from sentence_transformers import SentenceTransformer

from ..llm.base import LLM
from .router import route
from vectorstore.weaviate_store import WeaviateStore

_embed_model = SentenceTransformer("all-MiniLM-L6-v2")


def build_prompt(question: str, hits: list[dict]) -> str:
    ctx = "\n\n".join(
        [
            f"Source: {h['title']} ({h['url']})\n"
            f"Excerpt: {h['chunk']}"
            for h in hits
        ]
    )
    return f"""You are an enterprise architecture assistant.
Answer using ONLY the provided Confluence excerpts.
If insufficient, say: "I don't have enough information in Confluence."
Add citations as (URL) at the end of sentences.

Question:
{question}

Confluence Excerpts:
{ctx}

Answer:
"""


def answer(
    question: str,
    store: WeaviateStore,
    llm: LLM,
    space_key: Optional[str] = None,
    top_k: int = 8,
) -> Dict:
    tool = route(question)

    if tool == "confluence_decision_rag":
        qv = _embed_model.encode([question],
                                 normalize_embeddings=True)[0].tolist()
        hits = store.semantic_search(
            query_vector=qv,
            top_k=top_k,
            where_filter={"space_key": space_key} if space_key else None,
        )
        prompt = build_prompt(question, hits)
        response = llm.generate(prompt)
        return {"answer": response, "sources": hits}

    return {"answer": "No suitable tool found for this question.",
            "sources": []}
