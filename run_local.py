"""
Local pipeline runner — runs ingestion + extraction + analytics
against the local PostgreSQL instance without Docker or Dagster.

Usage:
    source .venv/bin/activate
    python run_local.py
"""

from __future__ import annotations

import os
from pathlib import Path

# Load .env and force-set all values so stale shell exports don't win
_env_file = Path(__file__).parent / ".env"
if _env_file.exists():
    for _line in _env_file.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            os.environ[_k.strip()] = _v.strip()

os.environ.setdefault("DATABASE_URL", "postgresql://pubmed:pubmed@localhost:5432/pubmed_pipeline")
os.environ.setdefault("GEMINI_MODEL", "gemini/gemini-flash-latest")
os.environ.setdefault("LLM_BATCH_SIZE", "16")

from rich.console import Console
from rich.table import Table

from src.db.queries import (
    bulk_upsert_articles,
    get_abstracts_without_extraction,
    save_analytics_result,
    upsert_extraction,
    upsert_raw_file,
)
from src.db.session import get_session_factory, init_db
from src.ingest.downloader import download_and_verify
from src.ingest.filter import filter_articles
from src.ingest.parser import parse_xml_file
from src.llm.extractor import run_extraction
from src.analytics.treatment_matrix import build_treatment_outcome_matrix
from src.analytics.publication_trends import publication_trends
from src.analytics.mesh_cooccurrence import mesh_cooccurrence
from src.analytics.geography import research_geography
from src.analytics.study_design import study_design_over_time
from src.analytics.knowledge_graph import build_knowledge_graph

console = Console()
DB_URL = os.environ["DATABASE_URL"]

# ── File numbers to ingest (highest = most recent; adjust as needed) ─────────
FILE_NUMBERS = list(range(1274, 1270, -1))  # 4 files
TARGET_ARTICLES = 200


def get_session():
    return get_session_factory(DB_URL)()


def step_init():
    console.rule("[bold blue]Step 1 — Init DB")
    init_db(DB_URL)
    console.print("[green]✓ Tables ready")


def step_ingest():
    console.rule("[bold blue]Step 2 — Ingest PubMed baseline files")
    session = get_session()
    total_inserted = 0

    for file_number in FILE_NUMBERS:
        from src.ingest.downloader import baseline_file_name
        from src.db.queries import file_already_ingested

        fname = baseline_file_name(file_number)
        if file_already_ingested(session, fname):
            console.print(f"[yellow]↷ {fname} already ingested — skipping")
            continue

        console.print(f"[cyan]↓ Downloading {fname} ...")
        try:
            xml_path, md5 = download_and_verify(file_number)
        except Exception as e:
            console.print(f"[red]✗ Download failed: {e}")
            continue

        all_articles = list(parse_xml_file(xml_path, source_file=fname))
        relevant = filter_articles(all_articles)
        console.print(f"  Parsed {len(all_articles):,} total → [green]{len(relevant)} endometriosis articles")

        inserted = bulk_upsert_articles(session, relevant)
        upsert_raw_file(session, fname, md5, len(all_articles))
        total_inserted += inserted
        console.print(f"  [green]✓ Inserted {inserted} new articles")

        if total_inserted >= TARGET_ARTICLES:
            console.print(f"[green]✓ Reached target of {TARGET_ARTICLES} articles — stopping")
            break

    session.close()
    console.print(f"[bold green]Total inserted: {total_inserted}")


def step_extract():
    console.rule("[bold blue]Step 3 — LLM Extraction (Gemini)")

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        console.print("[red]✗ GEMINI_API_KEY not set — skipping extraction")
        console.print("  Set it with: export GEMINI_API_KEY=your_key_here")
        return

    session = get_session()
    abstracts = get_abstracts_without_extraction(session, limit=10)
    console.print(f"  Extracting from {len(abstracts)} abstracts ...")

    success = 0
    errors = 0
    for i in range(0, len(abstracts), 16):
        batch = abstracts[i : i + 16]
        extractions = run_extraction(batch)
        for extraction in extractions:
            upsert_extraction(session, extraction)
            if extraction.extraction_error:
                errors += 1
            else:
                success += 1
        console.print(f"  Batch {i // 16 + 1}: {len(batch)} processed")

    session.close()
    console.print(f"[green]✓ Extracted: {success} success, {errors} errors")


def step_analytics():
    console.rule("[bold blue]Step 4 — Analytics")
    session = get_session()

    console.print("  Building treatment-outcome matrix ...")
    matrix = build_treatment_outcome_matrix(session)
    save_analytics_result(session, "treatment_outcome_matrix", matrix)
    console.print(f"  [green]✓ {len(matrix)} treatment-outcome pairs")

    console.print("  Building publication trends ...")
    trends = publication_trends(session)
    save_analytics_result(session, "publication_trend_analysis", trends)
    console.print(f"  [green]✓ {len(trends)} years of data")

    console.print("  Building MeSH co-occurrence ...")
    mesh = mesh_cooccurrence(session)
    save_analytics_result(session, "mesh_cooccurrence_network", mesh)
    console.print(f"  [green]✓ {len(mesh)} co-occurrence pairs")

    console.print("  Building research geography ...")
    geo = research_geography(session)
    save_analytics_result(session, "research_geography_analysis", geo)
    console.print(f"  [green]✓ {len(geo)} countries")

    console.print("  Building study design trends ...")
    designs = study_design_over_time(session)
    save_analytics_result(session, "study_design_trends", designs)
    console.print(f"  [green]✓ {len(designs)} years of study design data")

    console.print("  Building knowledge graph ...")
    kg = build_knowledge_graph(session)
    save_analytics_result(session, "knowledge_graph_data", kg)
    console.print(f"  [green]✓ {len(kg.get('nodes', []))} nodes, {len(kg.get('links', []))} edges")

    session.close()


def step_report():
    console.rule("[bold blue]Summary")
    session = get_session()

    from src.db.models import PubmedArticle, LlmExtraction, AnalyticsResult

    articles = session.query(PubmedArticle).count()
    extractions = session.query(LlmExtraction).count()
    errors = session.query(LlmExtraction).filter(LlmExtraction.extraction_error.isnot(None)).count()
    analytics = session.query(AnalyticsResult).count()
    session.close()

    table = Table(title="Pipeline State")
    table.add_column("Table", style="cyan")
    table.add_column("Count", style="green")
    table.add_row("pubmed_article", str(articles))
    table.add_row("llm_extraction (success)", str(extractions - errors))
    table.add_row("llm_extraction (errors)", str(errors))
    table.add_row("analytics_result", str(analytics))
    console.print(table)


if __name__ == "__main__":
    step_init()
    step_ingest()
    step_extract()
    step_analytics()
    step_report()
