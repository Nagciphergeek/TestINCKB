"""
services/vector_search.py
Semantic similarity search using sentence-transformers + FAISS.
Used to detect duplicate/similar KB articles before saving.
"""
import os
import numpy as np
from dotenv import load_dotenv

load_dotenv()
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def get_embedding(text: str) -> np.ndarray:
    """Return a numpy embedding vector for the given text."""
    model = _get_model()
    return model.encode([text], normalize_embeddings=True)[0]


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two L2-normalized vectors."""
    return float(np.dot(a, b))


def find_similar_articles(query_text: str, articles: list, threshold: float = 0.80) -> list:
    """
    Given a query text and a list of article dicts (with 'title' and 'article' keys),
    return articles whose combined title+article embedding has cosine similarity >= threshold.

    Args:
        query_text: The incident text or article text to compare against.
        articles:   List of dicts from kb_db.get_all_articles().
        threshold:  Similarity threshold (0-1). Default 0.80.

    Returns:
        List of (article_dict, similarity_score) tuples, sorted by score desc.
    """
    if not articles:
        return []

    try:
        import faiss
    except ImportError:
        return []  # graceful degradation if faiss not installed

    query_emb = get_embedding(query_text).astype("float32")

    # Build corpus embeddings
    corpus_texts = [f"{a['title']} {a.get('tags', '')}" for a in articles]
    corpus_embs  = np.array([get_embedding(t) for t in corpus_texts], dtype="float32")

    dim   = query_emb.shape[0]
    index = faiss.IndexFlatIP(dim)   # Inner product on normalized vectors = cosine
    index.add(corpus_embs)

    scores, indices = index.search(query_emb.reshape(1, -1), k=min(5, len(articles)))

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx >= 0 and score >= threshold:
            results.append((articles[idx], round(float(score), 3)))

    results.sort(key=lambda x: x[1], reverse=True)
    return results
