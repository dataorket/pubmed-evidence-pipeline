from __future__ import annotations

from collections import defaultdict

from sqlalchemy.orm import Session

from src.db.models import PubmedArticle


def mesh_cooccurrence(session: Session, min_count: int = 3) -> list[dict]:
    rows = (
        session.query(PubmedArticle.mesh_terms)
        .filter(PubmedArticle.mesh_terms.isnot(None))
        .all()
    )
    counts: dict[tuple[str, str], int] = defaultdict(int)
    for (mesh_terms,) in rows:
        terms = sorted({t.lower() for t in (mesh_terms or [])})
        for i, a in enumerate(terms):
            for b in terms[i + 1 :]:
                counts[(a, b)] += 1
    return [
        {"term_a": a, "term_b": b, "co_occurrence_count": c}
        for (a, b), c in sorted(counts.items(), key=lambda x: -x[1])
        if c >= min_count
    ]
