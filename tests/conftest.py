from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db.models import Base


@pytest.fixture(scope="session")
def in_memory_engine():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(in_memory_engine):
    factory = sessionmaker(bind=in_memory_engine)
    s = factory()
    yield s
    s.close()


@pytest.fixture
def mock_llm_response():
    return {
        "treatments": ["dienogest", "placebo"],
        "outcomes": ["pelvic pain", "dysmenorrhea"],
        "treatment_outcomes": [
            {"treatment": "dienogest", "outcome": "pelvic pain", "effect_direction": "positive"},
            {"treatment": "dienogest", "outcome": "dysmenorrhea", "effect_direction": "positive"},
        ],
        "study_design": "randomized_controlled_trial",
        "population": {
            "sex": "female",
            "age_group": None,
            "disease_stage": "III-IV",
            "sample_size": 100,
            "special_population": None,
        },
        "extraction_confidence": 0.92,
        "extraction_error": None,
    }
