from __future__ import annotations

import textwrap
from pathlib import Path

from src.ingest.parser import parse_xml_file

SAMPLE_XML = textwrap.dedent("""\
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE PubmedArticleSet PUBLIC "-//NLM//DTD PubMedArticle, 1st January 2024//EN" "">
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>99999999</PMID>
      <Article>
        <ArticleTitle>Dienogest for endometriosis</ArticleTitle>
        <Abstract>
          <AbstractText>Women with endometriosis were treated with dienogest.</AbstractText>
        </Abstract>
        <AuthorList>
          <Author>
            <LastName>Smith</LastName>
            <ForeName>Jane</ForeName>
          </Author>
        </AuthorList>
        <Language>eng</Language>
        <PublicationTypeList>
          <PublicationType>Journal Article</PublicationType>
        </PublicationTypeList>
        <Journal>
          <Title>Journal of Endometriosis</Title>
          <JournalIssue>
            <PubDate>
              <Year>2022</Year>
              <Month>03</Month>
              <Day>15</Day>
            </PubDate>
          </JournalIssue>
        </Journal>
      </Article>
      <MeshHeadingList>
        <MeshHeading>
          <DescriptorName>Endometriosis</DescriptorName>
        </MeshHeading>
      </MeshHeadingList>
    </MedlineCitation>
  </PubmedArticle>
</PubmedArticleSet>
""")


def test_parse_basic_fields(tmp_path: Path):
    xml_file = tmp_path / "test.xml"
    xml_file.write_text(SAMPLE_XML)
    articles = list(parse_xml_file(xml_file, source_file="test.xml"))
    assert len(articles) == 1
    a = articles[0]
    assert a.pubmed_id == "99999999"
    assert "dienogest" in a.title.lower()
    assert a.abstract is not None
    assert a.pub_date is not None
    assert a.pub_date.year == 2022
    assert "Endometriosis" in a.mesh_terms
    assert len(a.authors) == 1
    assert a.authors[0].last_name == "Smith"
