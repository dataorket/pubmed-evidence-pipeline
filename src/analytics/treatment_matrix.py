from __future__ import annotations

from collections import defaultdict

from sqlalchemy.orm import Session

from src.db.models import LlmExtraction, PubmedArticle


def build_treatment_outcome_matrix(session: Session) -> list[dict]:
    rows = session.query(LlmExtraction).filter(LlmExtraction.extraction_error.is_(None)).all()
    counts: dict[tuple[str, str], dict] = defaultdict(
        lambda: {"frequency": 0, "positive": 0, "negative": 0, "neutral": 0, "mixed": 0}
    )
    for row in rows:
        for to in (row.treatment_outcomes or []):
            key = (to["treatment"].lower(), to["outcome"].lower())
            counts[key]["frequency"] += 1
            direction = to.get("effect_direction", "unknown")
            if direction in counts[key]:
                counts[key][direction] += 1
    return [
        {
            "treatment": t,
            "outcome": o,
            **v,
        }
        for (t, o), v in sorted(counts.items(), key=lambda x: -x[1]["frequency"])
    ]
