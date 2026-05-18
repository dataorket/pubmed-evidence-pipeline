from __future__ import annotations

from dagster import (
    AssetExecutionContext,
    MaterializeResult,
    asset,
)

from src.dagster_pipeline.partitions import baseline_file_partitions
from src.dagster_pipeline.resources import DatabaseResource
from src.db.queries import (
    bulk_upsert_articles,
    file_already_ingested,
    upsert_raw_file,
)
from src.ingest.downloader import baseline_file_name, download_and_verify
from src.ingest.filter import filter_articles
from src.ingest.parser import parse_xml_file


@asset(
    partitions_def=baseline_file_partitions,
    group_name="ingestion",
    description="Download, verify, parse, and filter a PubMed baseline .xml.gz file",
)
def filtered_articles(context: AssetExecutionContext, database: DatabaseResource) -> MaterializeResult:
    file_number = int(context.partition_key)
    file_name = baseline_file_name(file_number)

    session = database.get_session()
    try:
        if file_already_ingested(session, file_name):
            context.log.info(f"{file_name} already ingested — skipping")
            return MaterializeResult(metadata={"status": "skipped", "file": file_name})

        context.log.info(f"Downloading {file_name}")
        xml_path, md5 = download_and_verify(file_number)

        context.log.info(f"Parsing {xml_path}")
        all_articles = list(parse_xml_file(xml_path, source_file=file_name))
        relevant = filter_articles(all_articles)

        context.log.info(f"Inserting {len(relevant)} articles (filtered from {len(all_articles)})")
        inserted = bulk_upsert_articles(session, relevant)
        upsert_raw_file(session, file_name=file_name, md5=md5, record_count=len(all_articles))

        return MaterializeResult(
            metadata={
                "file": file_name,
                "total_parsed": len(all_articles),
                "filtered": len(relevant),
                "inserted": inserted,
            }
        )
    finally:
        session.close()
