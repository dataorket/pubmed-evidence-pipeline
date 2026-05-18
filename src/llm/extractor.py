from __future__ import annotations

from src.llm.client import extract_treatment_outcomes_batch
from src.models import LLMExtraction, PopulationProfile, TreatmentOutcome


def parse_extraction(raw: dict) -> LLMExtraction:
    population_data = raw.get("population") or {}
    treatment_outcomes = [
        TreatmentOutcome(
            treatment=t.get("treatment", ""),
            outcome=t.get("outcome", ""),
            effect_direction=t.get("effect_direction", "unknown"),
        )
        for t in (raw.get("treatment_outcomes") or [])
        if t.get("treatment") and t.get("outcome")
    ]
    return LLMExtraction(
        pubmed_id=raw["pubmed_id"],
        treatments=raw.get("treatments") or [],
        outcomes=raw.get("outcomes") or [],
        treatment_outcomes=treatment_outcomes,
        study_design=raw.get("study_design") or "unknown",
        population=PopulationProfile(**{
            k: population_data.get(k)
            for k in PopulationProfile.model_fields
        }),
        extraction_confidence=float(raw.get("extraction_confidence") or 0.0),
        extraction_error=raw.get("extraction_error"),
    )


def run_extraction(abstracts: list[tuple[str, str]]) -> list[LLMExtraction]:
    raw_results = extract_treatment_outcomes_batch(abstracts)
    return [parse_extraction(r) for r in raw_results]
