from __future__ import annotations

from collections import Counter

from sqlalchemy.orm import Session

from src.db.models import LlmExtraction, PubmedArticle


def study_design_over_time(session: Session) -> list[dict]:
    rows = (
        session.query(PubmedArticle.pub_date, LlmExtraction.study_design)
        .join(LlmExtraction, PubmedArticle.pubmed_id == LlmExtraction.pubmed_id)
        .filter(PubmedArticle.pub_date.isnot(None))
        .all()
    )
    by_year: dict[int, Counter] = {}
    for pub_date, design in rows:
        year = pub_date.year
        if year not in by_year:
            by_year[year] = Counter()
        by_year[year][design or "unknown"] += 1
    return [
        {"year": year, "designs": dict(counter)}
        for year, counter in sorted(by_year.items())
    ]
