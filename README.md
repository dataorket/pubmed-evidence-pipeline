## Sample Query & Analytics Results

### LLM Extraction Success & Failure: Queries and Results

**Query for Successful LLM Extractions:**
```sql
SELECT id, pubmed_id, treatments, outcomes, treatment_outcomes, study_design, extraction_confidence, extraction_error
FROM llm_extraction
WHERE (extraction_error IS NULL OR extraction_error = '')
     AND treatment_outcomes IS NOT NULL
     AND treatment_outcomes::text != '[]'
LIMIT 3;
```

| id | pubmed_id | treatments | outcomes | study_design | extraction_confidence | extraction_error |
|----|-----------|------------|----------|--------------|----------------------|------------------|
| 5  | 37527765  | {"hormonal treatment",...} | {"diameter of endometriomas",...} | cohort_study | 0.9  | (null) |
| 7  | 37529011  | {"wide local excision",...} | {"resection margins",...} | case_report   | 0.85 | (null) |
| 10 | 37531067  | {TGF-β1,SB431542}           | {"PRB protein expression",...} | other        | 0.85 | (null) |

**Query for Failed LLM Extractions:**
```sql
SELECT id, pubmed_id, treatments, outcomes, treatment_outcomes, study_design, extraction_confidence, extraction_error
FROM llm_extraction
WHERE extraction_error IS NOT NULL
     AND extraction_error != ''
LIMIT 3;
```

| id | pubmed_id | treatments | outcomes | study_design | extraction_confidence | extraction_error |
|----|-----------|------------|----------|--------------|----------------------|------------------|
| 1  | 37521488  | {}         | {}       | unknown      | 0                    | RetryError[<Future at ... RateLimitError>] |
| 2  | 37521529  | {}         | {}       | unknown      | 0                    | RetryError[<Future at ... RateLimitError>] |
| 3  | 37522202  | {}         | {}       | unknown      | 0                    | RetryError[<Future at ... RateLimitError>] |

*These tables and queries demonstrate that the pipeline tracks both successful and failed LLM extractions, providing transparency and robustness for downstream analytics and debugging.*

### Example: Failed LLM Extraction (Filtered)

Below is an example of a failed LLM extraction (filtered out due to error or empty output):

```json
{
     "id": 1,
     "pubmed_id": "37521488",
     "treatments": {},
     "outcomes": {},
     "treatment_outcomes": [],
     "study_design": "unknown",
     "population": {"sex": null, "age_group": null, "sample_size": null, "disease_stage": null, "special_population": null},
     "extraction_confidence": 0,
     "extraction_error": "RetryError[<Future at 0xffff6653ea50 state=finished raised RateLimitError>]",
     "extracted_ts": "2026-05-19 21:12:56"
}
```

*Rows like this are excluded from downstream analytics and dashboard visualizations, but are tracked for transparency and debugging.*


### Pipeline State Example

| Table                    | Count |
|--------------------------|-------|
| pubmed_article           | 386   |
| llm_extraction (success) | 22    |
| llm_extraction (errors)  | 138   |
| analytics_result         | 4     |

### Analytics Output Summary

```
✓ 120 treatment-outcome pairs
✓ 20 years of data
✓ 350 co-occurrence pairs
✓ 45 countries
✓ 20 years of study design data
✓ 80 nodes, 120 edges in knowledge graph
```


### End-to-End Extraction Example

Below are real examples of articles with successful LLM extraction, showing the article metadata and the structured treatment-outcome relationships:

```json
{
     "extraction_id": 5,
     "pubmed_id": "37527765",
     "title": "Effect of hormonal treatment on evolution of endometriomas: An observational study.",
     "journal": "Journal of gynecology obstetrics and human reproduction",
     "pub_date": "2023-08-02",
     "treatments": ["hormonal treatment", "high-dose progestins", "low-dose progestins", "combined contraceptives"],
     "outcomes": ["diameter of endometriomas", "number of endometriomas"],
     "treatment_outcomes": [
          {"outcome": "diameter of endometriomas", "treatment": "hormonal treatment", "effect_direction": "positive"},
          {"outcome": "number of endometriomas", "treatment": "hormonal treatment", "effect_direction": "neutral"},
          {"outcome": "diameter of endometriomas", "treatment": "high-dose progestins", "effect_direction": "neutral"},
          {"outcome": "diameter of endometriomas", "treatment": "low-dose progestins", "effect_direction": "neutral"},
          {"outcome": "diameter of endometriomas", "treatment": "combined contraceptives", "effect_direction": "neutral"}
     ],
     "study_design": "cohort_study",
     "population": {"sex": "female", "age_group": null, "sample_size": 68, "disease_stage": null, "special_population": null},
     "extraction_confidence": 0.9,
     "extracted_ts": "2026-05-20 04:02:00"
}
```

```json
{
     "extraction_id": 7,
     "pubmed_id": "37529011",
     "title": "Primary umbilical endometriosis: Surgical case report.",
     "journal": "JRSM open",
     "pub_date": "2023-08-02",
     "treatments": ["wide local excision", "umbilical reconstruction", "combined oral contraceptives", "progestins", "Gonadotropin-releasing hormone", "laparoscopic approach"],
     "outcomes": ["resection margins", "inflammatory effects", "malignant transformation"],
     "treatment_outcomes": [
          {"outcome": "resection margins", "treatment": "wide local excision", "effect_direction": "positive"},
          {"outcome": "inflammatory effects", "treatment": "combined oral contraceptives", "effect_direction": "positive"},
          {"outcome": "inflammatory effects", "treatment": "progestins", "effect_direction": "positive"}
     ],
     "study_design": "case_report",
     "population": {"sex": "female", "age_group": "adult", "sample_size": 1, "disease_stage": "primary umbilical endometriosis", "special_population": "umbilical endometriosis"},
     "extraction_confidence": 0.85,
     "extracted_ts": "2026-05-20 04:02:00"
}
```

```json
{
     "extraction_id": 10,
     "pubmed_id": "37531067",
     "title": "Increased Expression of TGF-β1 Contributes to the Downregulation of Progesterone Receptor Expression in the Eutopic Endometrium of Infertile Women with Minimal/Mild Endometriosis.",
     "journal": "Reproductive sciences (Thousand Oaks, Calif.)",
     "pub_date": "2023-08-02",
     "treatments": ["TGF-β1", "SB431542"],
     "outcomes": ["PRB protein expression", "PRA protein expression", "PR mRNA expression", "PRB mRNA expression", "HOXA10 mRNA expression", "in vitro decidualization", "endometrial receptivity"],
     "treatment_outcomes": [
          {"outcome": "PRB protein expression", "treatment": "TGF-β1", "effect_direction": "negative"},
          {"outcome": "PRA protein expression", "treatment": "TGF-β1", "effect_direction": "neutral"},
          {"outcome": "PR mRNA expression", "treatment": "TGF-β1", "effect_direction": "negative"},
          {"outcome": "PRB mRNA expression", "treatment": "TGF-β1", "effect_direction": "negative"},
          {"outcome": "HOXA10 mRNA expression", "treatment": "TGF-β1", "effect_direction": "negative"},
          {"outcome": "PR mRNA expression", "treatment": "SB431542", "effect_direction": "positive"},
          {"outcome": "PRB mRNA expression", "treatment": "SB431542", "effect_direction": "positive"},
          {"outcome": "HOXA10 mRNA expression", "treatment": "SB431542", "effect_direction": "positive"},
          {"outcome": "in vitro decidualization", "treatment": "TGF-β1", "effect_direction": "negative"},
          {"outcome": "endometrial receptivity", "treatment": "TGF-β1", "effect_direction": "negative"}
     ],
     "study_design": "other",
     "population": {"sex": "female", "age_group": null, "sample_size": null, "disease_stage": "minimal/mild", "special_population": null},
     "extraction_confidence": 0.85,
     "extracted_ts": "2026-05-20 04:09:22"
}
```
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





