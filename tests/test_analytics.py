from __future__ import annotations

from unittest.mock import MagicMock

from src.analytics.treatment_matrix import build_treatment_outcome_matrix


def _mock_session_with_extractions(treatment_outcomes: list[list[dict]]):
    session = MagicMock()
    rows = []
    for tos in treatment_outcomes:
        row = MagicMock()
        row.treatment_outcomes = tos
        row.extraction_error = None
        rows.append(row)
    session.query.return_value.filter.return_value.all.return_value = rows
    return session


def test_treatment_outcome_matrix_counts():
    tos = [
        [{"treatment": "dienogest", "outcome": "pain", "effect_direction": "positive"}],
        [{"treatment": "dienogest", "outcome": "pain", "effect_direction": "positive"}],
        [{"treatment": "surgery", "outcome": "recurrence", "effect_direction": "negative"}],
    ]
    session = _mock_session_with_extractions(tos)
    result = build_treatment_outcome_matrix(session)
    assert len(result) >= 2
    top = result[0]
    assert top["treatment"] == "dienogest"
    assert top["outcome"] == "pain"
    assert top["frequency"] == 2


def test_treatment_outcome_matrix_empty():
    session = _mock_session_with_extractions([])
    result = build_treatment_outcome_matrix(session)
    assert result == []
