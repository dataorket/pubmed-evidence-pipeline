from __future__ import annotations

import os

from dagster import Definitions, load_assets_from_modules

from src.dagster_pipeline import assets as assets_module
from src.dagster_pipeline.resources import DatabaseResource, LitellmResource

all_assets = load_assets_from_modules([assets_module])

defs = Definitions(
    assets=all_assets,
    resources={
        "database": DatabaseResource(
            database_url=os.getenv("DATABASE_URL", "")
        ),
        "litellm_resource": LitellmResource(
            model=os.getenv("GEMINI_MODEL", "gemini/gemini-1.5-flash"),
            batch_size=int(os.getenv("LLM_BATCH_SIZE", "16")),
        ),
    },
)
