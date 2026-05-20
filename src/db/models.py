from __future__ import annotations

from sqlalchemy import (
    ARRAY,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class PubmedRaw(Base):
    __tablename__ = "pubmed_raw"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_name = Column(String(255), nullable=False, unique=True)
    md5_checksum = Column(String(32), nullable=False)
    record_count = Column(Integer, nullable=False, default=0)
    ingest_ts = Column(DateTime, server_default=func.now())


class PubmedArticle(Base):
    __tablename__ = "pubmed_article"
    __table_args__ = (UniqueConstraint("pubmed_id", name="uq_pubmed_article_id"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    pubmed_id = Column(String(20), nullable=False)
    title = Column(Text)
    abstract = Column(Text)
    journal = Column(String(512))
    pub_date = Column(Date)
    language = Column(String(10))
    publication_types = Column(ARRAY(Text), server_default="{}")
    mesh_terms = Column(ARRAY(Text), server_default="{}")
    source_file = Column(String(255), nullable=False)
    ingestion_ts = Column(DateTime, server_default=func.now())

    authors = relationship("PubmedAuthor", back_populates="article", cascade="all, delete-orphan")
    grants = relationship("PubmedGrant", back_populates="article", cascade="all, delete-orphan")
    extraction = relationship(
        "LlmExtraction",
        back_populates="article",
        uselist=False,
        cascade="all, delete-orphan",
    )


class PubmedAuthor(Base):
    __tablename__ = "pubmed_author"

    id = Column(Integer, primary_key=True, autoincrement=True)
    article_id = Column(
        Integer, ForeignKey("pubmed_article.id", ondelete="CASCADE"), nullable=False
    )
    last_name = Column(String(255))
    fore_name = Column(String(255))
    affiliation = Column(Text)
    country = Column(String(255))

    article = relationship("PubmedArticle", back_populates="authors")


class PubmedGrant(Base):
    __tablename__ = "pubmed_grant"

    id = Column(Integer, primary_key=True, autoincrement=True)
    article_id = Column(
        Integer, ForeignKey("pubmed_article.id", ondelete="CASCADE"), nullable=False
    )
    grant_id = Column(String(255))
    agency = Column(Text)
    country = Column(String(255))

    article = relationship("PubmedArticle", back_populates="grants")


class LlmExtraction(Base):
    __tablename__ = "llm_extraction"
    __table_args__ = (UniqueConstraint("pubmed_id", name="uq_llm_extraction_pubmed_id"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    pubmed_id = Column(
        String(20),
        ForeignKey("pubmed_article.pubmed_id", ondelete="CASCADE"),
        nullable=False,
    )
    treatments = Column(ARRAY(Text), server_default="{}")
    outcomes = Column(ARRAY(Text), server_default="{}")
    treatment_outcomes = Column(JSONB, server_default="[]")
    study_design = Column(String(50), default="unknown")
    population = Column(JSONB, server_default="{}")
    extraction_confidence = Column(Float, default=0.0)
    extraction_error = Column(Text)
    extracted_ts = Column(DateTime, server_default=func.now())

    # pgvector embedding column (added via migration)
    # embedding = Column(Vector(768))

    article = relationship("PubmedArticle", back_populates="extraction")


class AnalyticsResult(Base):
    __tablename__ = "analytics_result"
    __table_args__ = (UniqueConstraint("name", name="uq_analytics_result_name"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    payload = Column(JSONB, nullable=False)
    generated_ts = Column(DateTime, server_default=func.now())
