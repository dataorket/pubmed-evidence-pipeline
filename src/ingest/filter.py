from __future__ import annotations

from src.models import PubMedArticle

# Primary MeSH descriptor for endometriosis
CONDITION_MESH_TERMS = {
    "D004715",  # Endometriosis
    "Endometriosis",
}

# Broad keyword set for title/abstract fallback matching
CONDITION_KEYWORDS = frozenset(
    [
        "endometriosis",
        "endometrioma",
        "endometriotic",
        "adenomyosis",
    ]
)


def _matches_mesh(article: PubMedArticle) -> bool:
    mesh_lower = {m.lower() for m in article.mesh_terms}
    return bool(mesh_lower & {t.lower() for t in CONDITION_MESH_TERMS})


def _matches_keyword(article: PubMedArticle) -> bool:
    haystack = " ".join(
        filter(None, [article.title, article.abstract])
    ).lower()
    return any(kw in haystack for kw in CONDITION_KEYWORDS)


def is_relevant(article: PubMedArticle) -> bool:
    return _matches_mesh(article) or _matches_keyword(article)


def filter_articles(articles: list[PubMedArticle]) -> list[PubMedArticle]:
    return [a for a in articles if is_relevant(a)]
