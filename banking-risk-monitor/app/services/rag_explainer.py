"""A deliberately small, local Retrieval-Augmented Generation (RAG) example.

Embeddings turn text into numeric vectors where similar meanings are close together.
FAISS stores those vectors and finds nearest policies quickly.  We only *retrieve*;
the final explanation is a transparent template, not an ungrounded language model.
"""
from pathlib import Path
import numpy as np

POLICY_DIR = Path(__file__).resolve().parents[2] / "data" / "policies"
_texts, _names, _index, _encoder = [], [], None, None

def initialise():
    """Embed each policy once at startup, then create an inner-product FAISS index."""
    global _texts, _names, _index, _encoder
    if _index is not None: return
    from sentence_transformers import SentenceTransformer
    import faiss
    _encoder = SentenceTransformer("all-MiniLM-L6-v2")
    files = sorted(POLICY_DIR.glob("*.txt"))
    _names, _texts = [f.stem for f in files], [f.read_text(encoding="utf-8").strip() for f in files]
    vectors = _encoder.encode(_texts, normalize_embeddings=True).astype("float32")
    _index = faiss.IndexFlatIP(vectors.shape[1]) # cosine similarity, because normalized
    _index.add(vectors)

def explain(reasons: list[str], top_k: int = 3) -> dict:
    initialise()
    query = "; ".join(reasons) or "transaction risk manual review"
    vector = _encoder.encode([query], normalize_embeddings=True).astype("float32")
    scores, ids = _index.search(vector, min(top_k, len(_texts)))
    policies = [{"policy": _names[i], "text": _texts[i], "similarity": round(float(s), 3)} for s, i in zip(scores[0], ids[0]) if i >= 0]
    cited = "\n".join(f"- {p['policy']}: {p['text']}" for p in policies)
    action = "Escalate for manual review according to the retrieved policy requirements."
    return {"reasons": reasons, "policies": policies,
            "explanation": f"Flagged because: {', '.join(reasons) or 'model anomaly'}.\n\nRelevant policy evidence:\n{cited}\n\nRecommended action: {action}"}
