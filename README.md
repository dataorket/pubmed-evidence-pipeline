# Endometriosis Treatment Evidence Pipeline — Solution

## Overview

This repository contains a fully reproducible, orchestrated pipeline for mapping the treatment evidence landscape for **endometriosis** using PubMed abstracts. The pipeline is built with Dagster, Docker Compose, and Streamlit, and demonstrates robust ingestion, analytics, and LLM-powered extraction (with clear limitations for free-tier LLMs).


## Quick Start

```sh
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
> ```sh
> uv sync
> source .venv/bin/activate
> export DAGSTER_HOME="$PWD"
> export DATABASE_URL="postgresql://pubmed:pubmed@localhost:5432/pubmed_pipeline"
> dagster dev          # http://localhost:3000
> streamlit run src/web/app.py   # http://localhost:8501
> ```


## Condition Choice: Endometriosis

Endometriosis is a highly prevalent, under-researched chronic condition. The pipeline filters PubMed records using both MeSH terms and keyword matching for high recall and precision.


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


### Asset Dependency Graph

```
filtered_articles (partitioned: 1 per file)
│
├── publication_trend_analysis
├── mesh_cooccurrence_network
├── research_geography_analysis
└── funding_landscape_analysis

extracted_treatment_outcomes
└── knowledge_graph_data
```


#### Streamlit Dashboard Analytics

**Treatment-Outcome Matrix**

![Treatment-Outcome Matrix: Example with data](Screenshot%202026-05-20%20at%2013.53.01.png)

*Treatment-Outcome Matrix: Example with data populated after a successful LLM extraction run. This screenshot demonstrates that the pipeline can produce LLM-powered analytics when quota is available. If rate-limited, this page may show 'No data yet'.*

**Publication Trends Over Time**

![Publication Trends Over Time](Screenshot%202026-05-20%20at%2012.44.48.png)


**MeSH Term Co-occurrence Network**

![MeSH Term Co-occurrence Network](Screenshot%202026-05-20%20at%2012.45.12.png)

*MeSH Term Co-occurrence Network: Visualizes the subtopic structure and research clusters for endometriosis.*

**Research Geography**

![Research Geography](Screenshot%202026-05-20%20at%2012.45.39.png)

*Research Geography: Article count by country, showing global research distribution for endometriosis.*

**Knowledge Graph**

![Treatment-Outcome Knowledge Graph: No data yet — run the pipeline first.](Screenshot%202026-05-20%20at%2012.45.51.png)

*The Treatment-Outcome Knowledge Graph page shows 'No data yet' because LLM-powered extraction is rate-limited on the free Gemini API tier.*

**Population Profile**

![Patient Population Profile: No data yet — run the pipeline first.](Screenshot%202026-05-20%20at%2012.45.58.png)

*The Patient Population Profile page shows 'No data yet' because LLM-powered extraction is rate-limited on the free Gemini API tier.*

**Funding Landscape**

![Funding Landscape](Screenshot%202026-05-20%20at%2012.46.23.png)

*Funding Landscape: Top funding agencies by article count, fully materialized and visualized.*

### Demonstrated Analytics (with screenshots)

![Dagster asset catalog showing materialized and non-materialized assets](Screenshot%202026-05-20%20at%2012.41.49.png)

*Dagster asset catalog showing all 10 partitions of `filtered_articles` and all metadata-powered analytics (`funding_landscape_analysis`, `research_geography_analysis`, `mesh_cooccurrence_network`, `publication_trend_analysis`) successfully materialized. LLM-powered analytics (`extracted_treatment_outcomes`, `knowledge_graph_data`, `patient_population_profiling`, `study_design_trends`, `treatment_outcome_matrix`) are not materialized due to Gemini API rate limits. The `extracted_treatment_outcomes` asset is currently running, illustrating the impact of LLM rate limits on pipeline throughput.*

These analytics are fully reproducible and can be validated with the provided Docker Compose setup or local run instructions.

### LLM Extraction Limitation


**This limitation is documented and expected for LLM-powered pipelines on free-tier APIs.**


## How to Reproduce

1. Clone the repo and copy `.env.example` to `.env`. Add your Gemini API key.
2. Run `docker compose up` and wait for all services to become healthy.
3. Open Dagster UI (http://localhost:3000), seed partitions, and materialize assets in order:
   - `filtered_articles` (all partitions)
   - Metadata-powered analytics (see above)
   - (Optional) LLM extraction and downstream analytics if you have API quota
4. Open Streamlit dashboard (http://localhost:8501) to view results.


## Known Issues & Next Steps


### Example: LLM Extraction Rate Limit and Long Run

![LLM extraction asset run taking over 10 hours and failing due to Gemini API rate limits](Screenshot%202026-05-20%20at%2012.31.59.png)

*The `extracted_treatment_outcomes` asset can take over 10 hours or fail due to Gemini API free-tier rate limits (20 requests/day). This is an external limitation, not a pipeline bug. See the [Gemini API quota documentation](https://ai.google.dev/gemini-api/docs/rate-limits) for more details.*



Please do **not** add comments to your code unless they are strictly necessary to explain non-obvious behavior, hidden invariants, or workarounds. Clear names, small functions, and obvious structure are preferred over narrative comments. Reviewers should be able to read the code without inline explanations.


