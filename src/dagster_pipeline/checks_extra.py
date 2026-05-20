from dagster import AssetCheckResult, asset_check
from src.dagster_pipeline.resources import DatabaseResource
from src.db.models import PubmedArticle, LlmExtraction

@asset_check(asset="filtered_articles", description="No duplicate pubmed_id values allowed in pubmed_article")
def no_duplicate_pubmed_id_check(database: DatabaseResource) -> AssetCheckResult:
    with database.get_session() as session:
        total = session.query(PubmedArticle).count()
        unique = session.query(PubmedArticle.pubmed_id).distinct().count()
    return AssetCheckResult(
        passed=total == unique,
        metadata={"total": total, "unique_pubmed_id": unique, "duplicates": total - unique},
    )

@asset_check(asset="filtered_articles", description="No null titles allowed in pubmed_article")
def no_null_title_check(database: DatabaseResource) -> AssetCheckResult:
    with database.get_session() as session:
        nulls = session.query(PubmedArticle).filter(PubmedArticle.title.is_(None)).count()
    return AssetCheckResult(
        passed=nulls == 0,
        metadata={"null_titles": nulls},
    )

@asset_check(asset="llm_extraction", description="Extraction confidence must be between 0 and 1 for all rows")
def extraction_confidence_range_check(database: DatabaseResource) -> AssetCheckResult:
    with database.get_session() as session:
        out_of_range = session.query(LlmExtraction).filter(
            (LlmExtraction.extraction_confidence < 0) | (LlmExtraction.extraction_confidence > 1)
        ).count()
    return AssetCheckResult(
        passed=out_of_range == 0,
        metadata={"out_of_range_confidence": out_of_range},
    )
