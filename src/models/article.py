from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class Author(BaseModel):
    last_name: str | None = None
    fore_name: str | None = None
    affiliation: str | None = None
    country: str | None = None


class Grant(BaseModel):
    grant_id: str | None = None
    agency: str | None = None
    country: str | None = None


class PubMedArticle(BaseModel):
    pubmed_id: str
    title: str
    abstract: str | None = None
    authors: list[Author] = Field(default_factory=list)
    journal: str | None = None
    pub_date: date | None = None
    mesh_terms: list[str] = Field(default_factory=list)
    grants: list[Grant] = Field(default_factory=list)
    source_file: str
    language: str | None = None
    publication_types: list[str] = Field(default_factory=list)


StudyDesign = Literal[
    "randomized_controlled_trial",
    "cohort_study",
    "case_control",
    "meta_analysis",
    "systematic_review",
    "case_report",
    "narrative_review",
    "cross_sectional",
    "other",
    "unknown",
]

EffectDirection = Literal["positive", "negative", "neutral", "mixed", "unknown"]


class PopulationProfile(BaseModel):
    sex: str | None = None
    age_group: str | None = None
    disease_stage: str | None = None
    sample_size: int | None = None
    special_population: str | None = None


class TreatmentOutcome(BaseModel):
    treatment: str
    outcome: str
    effect_direction: EffectDirection = "unknown"


class LLMExtraction(BaseModel):
    pubmed_id: str
    treatments: list[str] = Field(default_factory=list)
    outcomes: list[str] = Field(default_factory=list)
    treatment_outcomes: list[TreatmentOutcome] = Field(default_factory=list)
    study_design: StudyDesign = "unknown"
    population: PopulationProfile = Field(default_factory=PopulationProfile)
    extraction_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    extraction_error: str | None = None
