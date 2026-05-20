from __future__ import annotations

from datetime import date

from src.ingest.filter import is_relevant
from src.models import PubMedArticle


def _article(**kwargs) -> PubMedArticle:
    defaults = dict(
        pubmed_id="12345",
        title="Test",
        abstract=None,
        authors=[],
        journal="Test Journal",
        pub_date=date(2020, 1, 1),
        mesh_terms=[],
        grants=[],
        source_file="test.xml",
        language="eng",
        publication_types=[],
    )
    return PubMedArticle(**(defaults | kwargs))


def test_matches_mesh_term():
    article = _article(mesh_terms=["Endometriosis", "Pain"])
    assert is_relevant(article)


def test_matches_keyword_in_title():
    article = _article(title="Laparoscopy for endometriosis treatment")
    assert is_relevant(article)


def test_matches_keyword_in_abstract():
    article = _article(abstract="Women with endometrioma were enrolled.")
    assert is_relevant(article)


def test_no_match():
    article = _article(
        title="Diabetes management in adults",
        abstract="This study examined insulin therapy.",
    )
    assert not is_relevant(article)


def test_case_insensitive_mesh():
    article = _article(mesh_terms=["ENDOMETRIOSIS"])
    assert is_relevant(article)
