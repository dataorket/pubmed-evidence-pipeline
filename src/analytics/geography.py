from __future__ import annotations

from collections import defaultdict

from sqlalchemy.orm import Session

from src.db.models import PubmedArticle, PubmedAuthor


def research_geography(session: Session) -> list[dict]:
    rows = (
        session.query(PubmedAuthor.country, PubmedArticle.pub_date)
        .join(PubmedArticle, PubmedAuthor.article_id == PubmedArticle.id)
        .filter(PubmedAuthor.country.isnot(None))
        .all()
    )
    by_country: dict[str, dict] = defaultdict(lambda: {"article_ids": set(), "years": []})
    for country, pub_date in rows:
        c = country.strip()
        if not c:
            continue
        by_country[c]["article_ids"].add(id)
        if pub_date:
            by_country[c]["years"].append(pub_date.year)
    return [
        {
            "country": country,
            "article_count": len(v["article_ids"]),
            "earliest_year": min(v["years"]) if v["years"] else None,
            "latest_year": max(v["years"]) if v["years"] else None,
        }
        for country, v in sorted(by_country.items(), key=lambda x: -len(x[1]["article_ids"]))
    ]
