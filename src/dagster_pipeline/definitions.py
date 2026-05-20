from __future__ import annotations

import os

from dagster import (
    AssetSelection,
    Definitions,
    define_asset_job,
    load_assets_from_modules,
)

from src.dagster_pipeline import assets as assets_module
from src.dagster_pipeline.resources import DatabaseResource, LitellmResource

all_assets = load_assets_from_modules([assets_module])

# ── Jobs ──────────────────────────────────────────────────────────────────────

# Run the full pipeline end-to-end for a selected partition of files.
# Trigger from Dagster UI → Jobs → full_pipeline_job → Launchpad.
full_pipeline_job = define_asset_job(
    name="full_pipeline_job",
    selection=AssetSelection.groups("ingestion", "extraction", "analytics"),
    description=(
        "Download & filter PubMed files, run LLM extraction, "
        "and recompute all analytics in one shot."
    ),
)

# Run only the LLM extraction + analytics (skips downloading).
extraction_and_analytics_job = define_asset_job(
    name="extraction_and_analytics_job",
    selection=AssetSelection.groups("extraction", "analytics"),
    description="Re-run LLM extraction on pending abstracts, then refresh analytics.",
)

# Run only analytics (fast, no LLM calls).
analytics_only_job = define_asset_job(
    name="analytics_only_job",
    selection=AssetSelection.groups("analytics"),
    description="Recompute all analytics from existing DB data.",
)

defs = Definitions(
    assets=all_assets,
    jobs=[full_pipeline_job, extraction_and_analytics_job, analytics_only_job],
    resources={
        "database": DatabaseResource(
            database_url=os.getenv("DATABASE_URL", "")
        ),
        "litellm_resource": LitellmResource(
            model=os.getenv("GEMINI_MODEL", "gemini/gemini-flash-latest"),
            batch_size=int(os.getenv("LLM_BATCH_SIZE", "16")),
        ),
    },
)
