from __future__ import annotations

from sqlalchemy.orm import Session

from src.db.models import (
    AnalyticsResult,
    LlmExtraction,
    PubmedArticle,
    PubmedAuthor,
    PubmedGrant,
    PubmedRaw,
)
from src.models import LLMExtraction, PubMedArticle


def upsert_raw_file(session: Session, file_name: str, md5: str, record_count: int) -> None:
    existing = session.query(PubmedRaw).filter_by(file_name=file_name).first()
    if existing:
        existing.record_count = record_count
    else:
        session.add(PubmedRaw(file_name=file_name, md5_checksum=md5, record_count=record_count))
    session.commit()


def file_already_ingested(session: Session, file_name: str) -> bool:
    return session.query(PubmedRaw).filter_by(file_name=file_name).first() is not None


def bulk_upsert_articles(session: Session, articles: list[PubMedArticle]) -> int:
    inserted = 0
    for article in articles:
        existing = session.query(PubmedArticle).filter_by(pubmed_id=article.pubmed_id).first()
        if existing:
            continue
        row = PubmedArticle(
            pubmed_id=article.pubmed_id,
            title=article.title,
            abstract=article.abstract,
            journal=article.journal,
            pub_date=article.pub_date,
            language=article.language,
            publication_types=article.publication_types,
            mesh_terms=article.mesh_terms,
            source_file=article.source_file,
        )
        session.add(row)
        session.flush()
        for a in article.authors:
            session.add(PubmedAuthor(article_id=row.id, **a.model_dump()))
        for g in article.grants:
            session.add(PubmedGrant(article_id=row.id, **g.model_dump()))
        inserted += 1
    session.commit()
    return inserted


def get_abstracts_without_extraction(session: Session, limit: int = 500) -> list[tuple[str, str]]:
    extracted_ids = session.query(LlmExtraction.pubmed_id)
    rows = (
        session.query(PubmedArticle.pubmed_id, PubmedArticle.abstract)
        .filter(PubmedArticle.abstract.isnot(None))
        .filter(PubmedArticle.pubmed_id.notin_(extracted_ids))
        .limit(limit)
        .all()
    )
    return [(r.pubmed_id, r.abstract) for r in rows]


def upsert_extraction(session: Session, extraction: LLMExtraction) -> None:
    existing = session.query(LlmExtraction).filter_by(pubmed_id=extraction.pubmed_id).first()
    data = dict(
        treatments=extraction.treatments,
        outcomes=extraction.outcomes,
        treatment_outcomes=[t.model_dump() for t in extraction.treatment_outcomes],
        study_design=extraction.study_design,
        population=extraction.population.model_dump(),
        extraction_confidence=extraction.extraction_confidence,
        extraction_error=extraction.extraction_error,
    )
    if existing:
        for k, v in data.items():
            setattr(existing, k, v)
    else:
        session.add(LlmExtraction(pubmed_id=extraction.pubmed_id, **data))
    session.commit()


def save_analytics_result(session: Session, name: str, payload: list | dict) -> None:
    existing = session.query(AnalyticsResult).filter_by(name=name).first()
    if existing:
        existing.payload = payload
    else:
        session.add(AnalyticsResult(name=name, payload=payload))
    session.commit()


def load_analytics_result(session: Session, name: str) -> list | dict | None:
    row = session.query(AnalyticsResult).filter_by(name=name).first()
    return row.payload if row else None
