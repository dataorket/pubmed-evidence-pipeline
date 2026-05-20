from __future__ import annotations

from dagster import MaterializeResult, asset

from src.analytics.funding import funding_landscape
from src.analytics.geography import research_geography
from src.analytics.knowledge_graph import build_knowledge_graph
from src.analytics.mesh_cooccurrence import mesh_cooccurrence
from src.analytics.population_profile import patient_population_profile
from src.analytics.publication_trends import publication_trends
from src.analytics.study_design import study_design_over_time
from src.analytics.treatment_matrix import build_treatment_outcome_matrix
from src.dagster_pipeline.resources import DatabaseResource
from src.db.queries import save_analytics_result


def _analytics_asset(name: str, fn, deps: list[str], description: str):
    @asset(deps=deps, group_name="analytics", description=description, name=name)
    def _asset(context, database: DatabaseResource) -> MaterializeResult:
        session = database.get_session()
        try:
            result = fn(session)
            save_analytics_result(session, name=name, payload=result)
            count = len(result) if isinstance(result, list) else len(result.get("nodes", []))
            return MaterializeResult(metadata={"row_count": count})
        finally:
            session.close()
    return _asset


treatment_outcome_matrix = _analytics_asset(
    "treatment_outcome_matrix",
    build_treatment_outcome_matrix,
    deps=["extracted_treatment_outcomes"],
    description="Treatment-outcome frequency matrix from LLM extractions",
)

study_design_trends = _analytics_asset(
    "study_design_trends",
    study_design_over_time,
    deps=["extracted_treatment_outcomes"],
    description="Study design distribution per year (LLM-powered)",
)

publication_trend_analysis = _analytics_asset(
    "publication_trend_analysis",
    publication_trends,
    deps=["filtered_articles"],
    description="Publication volume per year with study design breakdown",
)

mesh_cooccurrence_network = _analytics_asset(
    "mesh_cooccurrence_network",
    mesh_cooccurrence,
    deps=["filtered_articles"],
    description="MeSH term co-occurrence matrix",
)

research_geography_analysis = _analytics_asset(
    "research_geography_analysis",
    research_geography,
    deps=["filtered_articles"],
    description="Research output by country",
)

knowledge_graph_data = _analytics_asset(
    "knowledge_graph_data",
    build_knowledge_graph,
    deps=["extracted_treatment_outcomes"],
    description="Treatment-outcome-population knowledge graph triples",
)

patient_population_profiling = _analytics_asset(
    "patient_population_profiling",
    patient_population_profile,
    deps=["extracted_treatment_outcomes"],
    description="Patient population demographics extracted by LLM (age, sex, disease severity)",
)

funding_landscape_analysis = _analytics_asset(
    "funding_landscape_analysis",
    funding_landscape,
    deps=["filtered_articles"],
    description="Major funding agencies, grant counts, and temporal funding trends",
)
