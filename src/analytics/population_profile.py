from __future__ import annotations

from collections import defaultdict

from sqlalchemy.orm import Session

from src.db.models import LlmExtraction


def patient_population_profile(session: Session) -> list[dict]:
    rows = session.query(LlmExtraction).filter(LlmExtraction.extraction_error.is_(None)).all()

    age_counts: dict[str, int] = defaultdict(int)
    sex_counts: dict[str, int] = defaultdict(int)
    severity_counts: dict[str, int] = defaultdict(int)

    for row in rows:
        pop = row.population or {}
        age = (pop.get("age_group") or "").strip().lower()
        if age:
            age_counts[age] += 1

        sex = (pop.get("sex") or "").strip().lower()
        if sex:
            sex_counts[sex] += 1

        severity = (pop.get("disease_severity") or "").strip().lower()
        if severity:
            severity_counts[severity] += 1

    return [
        {
            "dimension": "age_group",
            "values": [{"label": k, "count": v} for k, v in sorted(age_counts.items(), key=lambda x: -x[1])],
        },
        {
            "dimension": "sex",
            "values": [{"label": k, "count": v} for k, v in sorted(sex_counts.items(), key=lambda x: -x[1])],
        },
        {
            "dimension": "disease_severity",
            "values": [{"label": k, "count": v} for k, v in sorted(severity_counts.items(), key=lambda x: -x[1])],
        },
    ]
