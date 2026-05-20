from __future__ import annotations

from unittest.mock import patch

from src.llm.extractor import parse_extraction, run_extraction


def test_parse_extraction_success(mock_llm_response):
    mock_llm_response["pubmed_id"] = "12345"
    result = parse_extraction(mock_llm_response)
    assert result.pubmed_id == "12345"
    assert "dienogest" in result.treatments
    assert result.study_design == "randomized_controlled_trial"
    assert result.population.sex == "female"
    assert result.population.sample_size == 100
    assert len(result.treatment_outcomes) == 2
    assert result.extraction_error is None


def test_parse_extraction_with_error():
    raw = {
        "pubmed_id": "99999",
        "treatments": [],
        "outcomes": [],
        "treatment_outcomes": [],
        "study_design": "unknown",
        "population": {},
        "extraction_confidence": 0.0,
        "extraction_error": "LLM timeout",
    }
    result = parse_extraction(raw)
    assert result.extraction_error == "LLM timeout"
    assert result.treatments == []


def test_run_extraction_uses_batch(mock_llm_response):
    mock_llm_response["pubmed_id"] = "11111"
    with patch(
        "src.llm.extractor.extract_treatment_outcomes_batch",
        return_value=[mock_llm_response],
    ):
        results = run_extraction([("11111", "Some abstract text about endometriosis treatment.")])
    assert len(results) == 1
    assert results[0].pubmed_id == "11111"
