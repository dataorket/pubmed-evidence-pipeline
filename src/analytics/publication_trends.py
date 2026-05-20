from __future__ import annotations

from sqlalchemy.orm import Session

from src.db.models import LlmExtraction, PubmedArticle


def publication_trends(session: Session) -> list[dict]:
    rows = (
        session.query(PubmedArticle.pub_date, LlmExtraction.study_design)
        .outerjoin(LlmExtraction, PubmedArticle.pubmed_id == LlmExtraction.pubmed_id)
        .filter(PubmedArticle.pub_date.isnot(None))
        .all()
    )
    by_year: dict[int, dict] = {}
    for pub_date, design in rows:
        year = pub_date.year
        if year not in by_year:
            by_year[year] = {
                "article_count": 0,
                "rct_count": 0,
                "review_count": 0,
                "case_report_count": 0,
            }
        by_year[year]["article_count"] += 1
        if design == "randomized_controlled_trial":
            by_year[year]["rct_count"] += 1
        elif design in ("systematic_review", "meta_analysis", "narrative_review"):
            by_year[year]["review_count"] += 1
        elif design == "case_report":
            by_year[year]["case_report_count"] += 1
    return [{"year": y, **v} for y, v in sorted(by_year.items())]
