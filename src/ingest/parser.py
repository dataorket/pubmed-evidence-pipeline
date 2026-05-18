from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Iterator

from lxml import etree

from src.models import Author, Grant, PubMedArticle


def _text(element: etree._Element, xpath: str) -> str | None:
    nodes = element.xpath(xpath)
    return nodes[0].strip() if nodes else None


def _texts(element: etree._Element, xpath: str) -> list[str]:
    return [n.strip() for n in element.xpath(xpath) if n.strip()]


def _parse_date(article: etree._Element) -> date | None:
    for path in [
        ".//PubMedPubDate[@PubStatus='pubmed']",
        ".//PubDate",
        ".//ArticleDate",
    ]:
        node = article.find(path)
        if node is None:
            continue
        try:
            year = int(node.findtext("Year") or 0)
            month = int(node.findtext("Month") or 1)
            day = int(node.findtext("Day") or 1)
            if year:
                return date(year, max(1, min(month, 12)), max(1, min(day, 28)))
        except (ValueError, TypeError):
            continue
    return None


def _parse_authors(article: etree._Element) -> list[Author]:
    authors = []
    for author in article.findall(".//Author"):
        affiliation_nodes = author.findall(".//AffiliationInfo/Affiliation")
        affiliation = affiliation_nodes[0].text if affiliation_nodes else None
        authors.append(
            Author(
                last_name=author.findtext("LastName"),
                fore_name=author.findtext("ForeName"),
                affiliation=affiliation,
                country=None,
            )
        )
    return authors


def _parse_grants(article: etree._Element) -> list[Grant]:
    grants = []
    for grant in article.findall(".//Grant"):
        grants.append(
            Grant(
                grant_id=grant.findtext("GrantID"),
                agency=grant.findtext("Agency"),
                country=grant.findtext("Country"),
            )
        )
    return grants


def _parse_abstract(article: etree._Element) -> str | None:
    parts = article.findall(".//AbstractText")
    if not parts:
        return None
    texts = []
    for part in parts:
        label = part.get("Label")
        text = "".join(part.itertext()).strip()
        if text:
            texts.append(f"{label}: {text}" if label else text)
    return " ".join(texts) if texts else None


def parse_xml_file(xml_path: Path, source_file: str) -> Iterator[PubMedArticle]:
    context = etree.iterparse(str(xml_path), events=("end",), tag="PubmedArticle", recover=True)
    for _, element in context:
        try:
            pubmed_id = element.findtext(".//PMID")
            if not pubmed_id:
                continue
            yield PubMedArticle(
                pubmed_id=pubmed_id,
                title=_text(element, ".//ArticleTitle/text()") or "",
                abstract=_parse_abstract(element),
                authors=_parse_authors(element),
                journal=element.findtext(".//Journal/Title"),
                pub_date=_parse_date(element),
                mesh_terms=_texts(element, ".//MeshHeading/DescriptorName/text()"),
                grants=_parse_grants(element),
                source_file=source_file,
                language=element.findtext(".//Language"),
                publication_types=_texts(element, ".//PublicationType/text()"),
            )
        except Exception:
            pass
        finally:
            element.clear()
