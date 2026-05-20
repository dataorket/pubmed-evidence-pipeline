from __future__ import annotations

from collections import defaultdict

from sqlalchemy.orm import Session

from src.db.models import PubmedArticle, PubmedGrant


def funding_landscape(session: Session) -> list[dict]:
    rows = (
        session.query(PubmedGrant.agency, PubmedGrant.country, PubmedArticle.pub_date)
        .join(PubmedArticle, PubmedGrant.article_id == PubmedArticle.id)
        .filter(PubmedGrant.agency.isnot(None))
        .all()
    )

    by_agency: dict[str, dict] = defaultdict(
        lambda: {
            "article_count": 0,
            "country": None,
            "years": [],
        }
    )
    for agency, country, pub_date in rows:
        a = agency.strip()
        if not a:
            continue
        by_agency[a]["article_count"] += 1
        if country and not by_agency[a]["country"]:
            by_agency[a]["country"] = country.strip()
        if pub_date:
            by_agency[a]["years"].append(pub_date.year)

    return [
        {
            "agency": agency,
            "article_count": v["article_count"],
            "country": v["country"],
            "earliest_year": min(v["years"]) if v["years"] else None,
            "latest_year": max(v["years"]) if v["years"] else None,
        }
        for agency, v in sorted(by_agency.items(), key=lambda x: -x[1]["article_count"])
    ]
