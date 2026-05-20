from __future__ import annotations

import networkx as nx
from sqlalchemy.orm import Session

from src.db.models import LlmExtraction


def build_knowledge_graph(session: Session) -> dict:
    rows = session.query(LlmExtraction).filter(LlmExtraction.extraction_error.is_(None)).all()
    G = nx.DiGraph()
    for row in rows:
        population = row.population or {}
        pop_label = population.get("disease_stage") or population.get("sex") or "general"
        for to in (row.treatment_outcomes or []):
            treatment = to.get("treatment", "").lower()
            outcome = to.get("outcome", "").lower()
            direction = to.get("effect_direction", "unknown")
            if not treatment or not outcome:
                continue
            G.add_node(treatment, type="treatment")
            G.add_node(outcome, type="outcome")
            G.add_edge(
                treatment,
                outcome,
                effect_direction=direction,
                population=pop_label,
                pubmed_id=row.pubmed_id,
            )
    data = nx.node_link_data(G)
    data["links"] = data.pop("edges", data.get("links", []))
    return data
