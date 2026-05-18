from __future__ import annotations

from pydantic import BaseModel


class TreatmentOutcomeRow(BaseModel):
    treatment: str
    outcome: str
    frequency: int
    positive_count: int
    negative_count: int
    neutral_count: int
    mixed_count: int


class PublicationTrendRow(BaseModel):
    year: int
    article_count: int
    rct_count: int
    review_count: int
    case_report_count: int


class MeshCooccurrenceRow(BaseModel):
    term_a: str
    term_b: str
    co_occurrence_count: int


class GeographyRow(BaseModel):
    country: str
    article_count: int
    earliest_year: int | None
    latest_year: int | None


class FundingRow(BaseModel):
    agency: str
    grant_count: int
    article_count: int


class KnowledgeGraphTriple(BaseModel):
    treatment: str
    outcome: str
    population_sex: str | None
    population_age_group: str | None
    disease_stage: str | None
    effect_direction: str
    pubmed_id: str
