from __future__ import annotations

from dagster import MaterializeResult, asset

from src.dagster_pipeline.resources import DatabaseResource, LitellmResource
from src.db.queries import get_abstracts_without_extraction, upsert_extraction
from src.llm.extractor import run_extraction


@asset(
    deps=["filtered_articles"],
    group_name="extraction",
    description="Run LLM extraction on unprocessed abstracts using Gemini via litellm",
)
def extracted_treatment_outcomes(
    context,
    database: DatabaseResource,
    litellm_resource: LitellmResource,
) -> MaterializeResult:
    session = database.get_session()
    try:
        batch_size = litellm_resource._batch_size()
        abstracts = get_abstracts_without_extraction(session, limit=5000)
        context.log.info(f"Extracting from {len(abstracts)} abstracts in batches of {batch_size}")

        total_extracted = 0
        total_errors = 0
        for i in range(0, len(abstracts), batch_size):
            batch = abstracts[i : i + batch_size]
            extractions = run_extraction(batch)
            for extraction in extractions:
                upsert_extraction(session, extraction)
                if extraction.extraction_error:
                    total_errors += 1
                else:
                    total_extracted += 1

        return MaterializeResult(
            metadata={
                "total_processed": len(abstracts),
                "successful": total_extracted,
                "errors": total_errors,
                "failure_rate": round(total_errors / max(len(abstracts), 1), 3),
            }
        )
    finally:
        session.close()
