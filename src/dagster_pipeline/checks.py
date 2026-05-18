from __future__ import annotations

from dagster import AssetCheckResult, AssetCheckSpec, asset_check

from src.dagster_pipeline.resources import DatabaseResource
from src.db.models import LlmExtraction, PubmedArticle


@asset_check(asset="extracted_treatment_outcomes", description="Extraction failure rate must be below 20%")
def extraction_failure_rate_check(database: DatabaseResource) -> AssetCheckResult:
    with database.get_session() as session:
        total = session.query(LlmExtraction).count()
        failed = session.query(LlmExtraction).filter(LlmExtraction.extraction_error.isnot(None)).count()
    if total == 0:
        return AssetCheckResult(passed=False, metadata={"reason": "No extractions found"})
    failure_rate = failed / total
    return AssetCheckResult(
        passed=failure_rate < 0.2,
        metadata={"total": total, "failed": failed, "failure_rate": round(failure_rate, 3)},
    )


@asset_check(asset="filtered_articles", description="At least 500 articles must be ingested")
def minimum_article_volume_check(database: DatabaseResource) -> AssetCheckResult:
    with database.get_session() as session:
        count = session.query(PubmedArticle).count()
    return AssetCheckResult(
        passed=count >= 500,
        metadata={"article_count": count},
    )
