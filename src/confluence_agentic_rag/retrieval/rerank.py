from typing import Dict, List
import numpy as np
from sentence_transformers import SentenceTransformer

_model = SentenceTransformer("all-MiniLM-L6-v2")


def rerank(question: str, items: List[Dict], top_k: int = 8) -> List[Dict]:
    if not items:
        return []
    qv = _model.encode([question], normalize_embeddings=True)[0]
    cv = _model.encode([it["chunk"] for it in items],
                       normalize_embeddings=True)
    scores = cv @ qv
    idx = np.argsort(-scores)[:top_k]
    out = []
    for i in idx:
        out.append({**items[i], "score": float(scores[i])})
    return out
