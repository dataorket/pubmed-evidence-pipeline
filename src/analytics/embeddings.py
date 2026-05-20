from __future__ import annotations

import os

import numpy as np
from sqlalchemy.orm import Session

from src.db.models import PubmedArticle


def compute_embeddings(session: Session) -> list[dict]:
    import litellm

    rows = (
        session.query(PubmedArticle.pubmed_id, PubmedArticle.abstract)
        .filter(PubmedArticle.abstract.isnot(None))
        .all()
    )
    pubmed_ids = [r.pubmed_id for r in rows]
    abstracts = [r.abstract for r in rows]

    model = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini/text-embedding-004")
    response = litellm.embedding(model=model, input=abstracts)
    vectors = np.array([e["embedding"] for e in response.data], dtype=np.float32)
    return [
        {"pubmed_id": pid, "embedding": vec.tolist()}
        for pid, vec in zip(pubmed_ids, vectors, strict=False)
    ]


def cluster_embeddings(embeddings: list[dict]) -> list[dict]:
    import hdbscan
    import umap

    vectors = np.array([e["embedding"] for e in embeddings], dtype=np.float32)
    reducer = umap.UMAP(n_components=2, random_state=42)
    reduced = reducer.fit_transform(vectors)
    clusterer = hdbscan.HDBSCAN(min_cluster_size=10)
    labels = clusterer.fit_predict(reduced)
    return [
        {
            "pubmed_id": e["pubmed_id"],
            "umap_x": float(reduced[i, 0]),
            "umap_y": float(reduced[i, 1]),
            "cluster": int(labels[i]),
        }
        for i, e in enumerate(embeddings)
    ]
