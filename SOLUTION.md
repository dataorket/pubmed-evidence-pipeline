# Solution: Endometriosis Treatment Evidence Pipeline

> This file documents the solution to the challenge specified in [`README.md`](./README.md).
> It covers all required deliverable sections: setup instructions, architecture overview,
> condition choice, prompt design decisions, analytics design decisions, and example output.

---

## Quick Start

```bash
# 1. Copy and fill in credentials
cp .env.example .env
# edit .env: set GEMINI_API_KEY

# 2. Start the full stack
docker compose up

# 3. Open Dagster UI — seed partitions, then materialize assets
open http://localhost:3000

# 4. View the dashboard
open http://localhost:8501
```

> **Local development (without Docker):**
> ```bash
> uv sync
> source .venv/bin/activate
> export $(grep -v '^#' .env | xargs)
> dagster dev          # http://localhost:3000
> streamlit run src/web/app.py   # http://localhost:8501
> ```

---

## Condition Choice: Endometriosis

Endometriosis affects ~10% of women of reproductive age globally and is chronically under-researched relative to its disease burden. It has a rich treatment landscape spanning hormonal therapies (GnRH agonists, progestins, combined OCP), surgical interventions (laparoscopic excision), and emerging biologics — making it an ideal condition for treatment-evidence mapping.

### Filtering strategy

Records are filtered after XML parsing using:
- **MeSH term presence** — `Endometriosis` descriptor in the article's MeSH list
- **Title/abstract keyword match** — any of `endometriosis`, `endometrioma`, `adenomyosis`

This two-signal approach minimizes false negatives (MeSH alone misses some relevant abstracts) while keeping false positives low.

### Volume

101 PubMed baseline files (1200–1300) were ingested, scanning ~3M total records and yielding **4,000+ endometriosis-relevant articles** — comfortably within the 2,000–5,000 target. Files are downloaded from the highest-numbered (most recent) end of the baseline.

---

## Architecture

```
PubMed FTP (XML.gz)
        │
        ▼
┌─────────────────────┐
│  Ingestion Assets   │  download → verify MD5 → parse XML → filter → PostgreSQL
│  (src/ingest/)      │  partitioned: one Dagster partition per .xml.gz file
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Extraction Asset   │  abstract text → Gemini → structured JSON → PostgreSQL
│  (src/llm/)         │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Analytics Assets   │  8 analytics: 4 LLM-powered + 4 metadata-powered
│  (src/analytics/)   │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Streamlit Dashboard│  7-page interactive dashboard
│  (src/web/app.py)   │
└─────────────────────┘
```

### Asset dependency graph

```
filtered_articles (partitioned: 1 per file)
      │                          │
      │                          ├── publication_trend_analysis
      │                          ├── mesh_cooccurrence_network
      │                          ├── research_geography_analysis
      │                          └── funding_landscape_analysis
      │
extracted_treatment_outcomes
      │
      ├── treatment_outcome_matrix
      ├── study_design_trends
      ├── patient_population_profiling
      └── knowledge_graph_data
```

### Dagster Jobs

| Job | What it runs |
|---|---|
| `full_pipeline_job` | Ingestion + extraction + all analytics |
| `extraction_and_analytics_job` | LLM extraction + all analytics (no download) |
| `analytics_only_job` | Recompute all analytics only (fast, no LLM) |

---

## Database Schema

| Table | Purpose |
|---|---|
| `pubmed_raw` | Tracks ingested `.xml.gz` files (file name, MD5, record count) |
| `pubmed_article` | Parsed article records (title, abstract, journal, pub_date, MeSH, language) |
| `pubmed_author` | Per-author rows linked to articles (name, affiliation, country) |
| `pubmed_grant` | Grant funding records per article (agency, grant ID, country) |
| `llm_extraction` | LLM output per abstract (treatments, outcomes, study design, population, confidence) |
| `analytics_result` | Key-value store for analytics payloads (JSONB), one row per named analytic |

**Schema design rationale:** `pubmed_author` and `pubmed_grant` are normalized into separate tables (not JSONB arrays) to support SQL-level geography and funding queries without unnesting. `analytics_result` uses JSONB for flexibility — analytics have heterogeneous shapes (list of dicts, graph dict, etc.) and are read whole by the dashboard.

---

## Prompt Design

Prompt: `src/llm/prompts/treatment_outcome.md`

The prompt extracts a structured JSON object from each abstract:

```json
{
  "treatments": ["dienogest", "laparoscopic excision"],
  "outcomes": ["pelvic pain reduction", "recurrence rate"],
  "treatment_outcomes": [
    {"treatment": "dienogest", "outcome": "pelvic pain reduction", "effect_direction": "positive"}
  ],
  "study_design": "randomized_controlled_trial",
  "population": {"sex": "female", "age_group": "reproductive-age", "disease_severity": "moderate-severe"},
  "extraction_confidence": 0.9
}
```

**Key design decisions:**

1. **Specific drug names over class names** — the prompt instructs the model to prefer `dienogest` over `progestin`, enabling treatment-level aggregation rather than class-level.
2. **Constrained effect direction enum** — `positive / negative / neutral / mixed / unknown` makes downstream aggregation tractable and avoids free-text noise.
3. **Extract only what is stated** — the prompt explicitly forbids inference to reduce hallucination in clinical contexts.
4. **`response_format={"type": "json_object"}`** — enforces structured output without post-processing heuristics.
5. **Worked example in prompt** — a full input/output pair anchors the model to the expected schema.

**Limitations:** Short abstracts, errata, and correction notices produce low-confidence extractions. Abstracts describing treatment comparisons may have ambiguous effect direction. Clinical accuracy is not guaranteed.

---

## Analytics Implemented

### LLM-Powered

| Asset | Description |
|---|---|
| `treatment_outcome_matrix` | Frequency heatmap of treatment × outcome co-occurrence with effect direction breakdown |
| `study_design_trends` | Distribution of RCTs, reviews, cohorts, case reports per year |
| `patient_population_profiling` | Age group, sex, disease severity distributions extracted from abstracts |
| `knowledge_graph_data` | Treatment-outcome-population triples stored as a NetworkX directed graph |

### Metadata-Powered

| Asset | Description |
|---|---|
| `publication_trend_analysis` | Article volume per year with study design overlay |
| `mesh_cooccurrence_network` | Co-occurring MeSH descriptor pairs ranked by frequency |
| `research_geography_analysis` | Article count by country derived from author affiliations |
| `funding_landscape_analysis` | Top funding agencies ranked by article count, with country and year range |

**Limitations:**
- Geography extraction uses affiliation text heuristics (last comma-separated token). Multi-country affiliations are attributed to one country.
- MeSH co-occurrence includes all MeSH terms — filtering to endometriosis-specific descriptors would sharpen the signal.
- LLM extraction is rate-limited by the free Gemini tier (~1 req/6s). A paid key would process all 4,000+ abstracts in ~15 minutes.

---

## Bonus Features Implemented

| Feature | Notes |
|---|---|
| ✅ Dagster Partitions | One partition per `.xml.gz` file — supports incremental ingestion and selective re-processing |
| ✅ Dagster Asset Checks | Defined in `src/dagster_pipeline/checks.py` |
| ✅ Streamlit Dashboard | 7 interactive pages covering all 8 analytics |
| ✅ Knowledge Graph | NetworkX directed graph with treatment → outcome edges, queryable by treatment or outcome |

---

## Environment Variables

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `GEMINI_API_KEY` | Google AI Studio API key (free at https://aistudio.google.com/apikey) |
| `GEMINI_MODEL` | litellm model identifier (default: `gemini/gemini-flash-latest`) |
| `LLM_BATCH_SIZE` | Abstracts per extraction batch (default: `8`) |
| `DAGSTER_HOME` | Absolute path to repo root (local dev only — not needed in Docker) |
| `DAGSTER_POSTGRES_*` | Dagster metadata DB connection (same DB as pipeline data) |

---

## Tests

```bash
uv run pytest tests/ -v
```

Tests cover: XML parsing, condition filtering, downloader MD5 verification, LLM extractor output schema, and analytics logic.

---

## Project Structure

```
src/
├── ingest/          # Downloader, XML parser, condition filter
├── llm/             # Gemini client, extraction prompt, response parser
│   └── prompts/     # treatment_outcome.md
├── analytics/       # 8 analytics functions (pure, session-injected)
├── dagster_pipeline/
│   ├── assets/      # Dagster asset definitions (ingestion, extraction, analytics)
│   ├── resources.py # DatabaseResource, LitellmResource
│   ├── definitions.py # Defs + 3 jobs
│   └── partitions.py
├── db/              # SQLAlchemy models, session factory, query helpers
├── models/          # Pydantic data models (PubMedArticle, LLMExtraction)
└── web/             # Streamlit dashboard (7 pages)
seed_partitions.py   # CLI tool to register partition keys in Dagster
workspace.docker.yaml # gRPC workspace config for Docker
workspace.yaml       # python_module workspace config for local dev
```
