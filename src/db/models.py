from __future__ import annotations

from sqlalchemy import (
    ARRAY,
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
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class PubmedRaw(Base):
    __tablename__ = "pubmed_raw"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    md5_checksum: Mapped[str] = mapped_column(String(32), nullable=False)
    record_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ingest_ts: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())


class PubmedArticle(Base):
    __tablename__ = "pubmed_article"
    __table_args__ = (UniqueConstraint("pubmed_id", name="uq_pubmed_article_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pubmed_id: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str | None] = mapped_column(Text)
    abstract: Mapped[str | None] = mapped_column(Text)
    journal: Mapped[str | None] = mapped_column(String(512))
    pub_date: Mapped[Date | None] = mapped_column(Date)
    language: Mapped[str | None] = mapped_column(String(10))
    publication_types: Mapped[list[str]] = mapped_column(ARRAY(Text), server_default="{}")
    mesh_terms: Mapped[list[str]] = mapped_column(ARRAY(Text), server_default="{}")
    source_file: Mapped[str] = mapped_column(String(255), nullable=False)
    ingestion_ts: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

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

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    article_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("pubmed_article.id", ondelete="CASCADE"),
        nullable=False,
    )
    last_name: Mapped[str | None] = mapped_column(String(255))
    fore_name: Mapped[str | None] = mapped_column(String(255))
    affiliation: Mapped[str | None] = mapped_column(Text)
    country: Mapped[str | None] = mapped_column(String(255))

    article = relationship("PubmedArticle", back_populates="authors")


class PubmedGrant(Base):
    __tablename__ = "pubmed_grant"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    article_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("pubmed_article.id", ondelete="CASCADE"),
        nullable=False,
    )
    grant_id: Mapped[str | None] = mapped_column(String(255))
    agency: Mapped[str | None] = mapped_column(Text)
    country: Mapped[str | None] = mapped_column(String(255))

    article = relationship("PubmedArticle", back_populates="grants")


class LlmExtraction(Base):
    __tablename__ = "llm_extraction"
    __table_args__ = (UniqueConstraint("pubmed_id", name="uq_llm_extraction_pubmed_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pubmed_id: Mapped[str] = mapped_column(
        String(20),
        ForeignKey("pubmed_article.pubmed_id", ondelete="CASCADE"),
        nullable=False,
    )
    treatments: Mapped[list[str]] = mapped_column(ARRAY(Text), server_default="{}")
    outcomes: Mapped[list[str]] = mapped_column(ARRAY(Text), server_default="{}")
    treatment_outcomes: Mapped[list[dict]] = mapped_column(JSONB, server_default="[]")
    study_design: Mapped[str] = mapped_column(String(50), default="unknown")
    population: Mapped[dict] = mapped_column(JSONB, server_default="{}")
    extraction_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    extraction_error: Mapped[str | None] = mapped_column(Text)
    extracted_ts: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

    # pgvector embedding column (added via migration)
    # embedding = Column(Vector(768))

    article = relationship("PubmedArticle", back_populates="extraction")


class AnalyticsResult(Base):
    __tablename__ = "analytics_result"
    __table_args__ = (UniqueConstraint("name", name="uq_analytics_result_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    payload: Mapped[list | dict] = mapped_column(JSONB, nullable=False)
    generated_ts: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
