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


Endometriosis was chosen as the target condition for this pipeline because:

- It is a highly prevalent, under-researched chronic disease affecting millions of women worldwide.
- The treatment landscape is complex, spanning hormonal therapies, surgical interventions, and emerging biologics—making it ideal for evidence mapping and analytics.
- Endometriosis is often underrepresented in research relative to its disease burden, so mapping the evidence landscape has real clinical value.
- PubMed contains a rich set of abstracts on endometriosis, enabling meaningful analytics and LLM-powered extraction.

The pipeline filters PubMed records using both MeSH terms and keyword matching for high recall and precision.


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

## Pipeline Orchestration & LLM Extraction Limitations

### Dagster / Streamlit UI: Asset Orchestration & Monitoring
Below are screenshots illustrating key pipeline and asset orchestration stages in Dagster:

- Asset materialization:
  ![Dagster asset materialization](Screenshot%202026-05-20%20at%2012.41.49.png)
  *Materialization of a partitioned asset in Dagster, showing being/not materialized and successful ingestion of a PubMed XML file.*
- Publication trends:
  ![Dagster asset checks](Screenshot%202026-05-20%20at%2012.44.48.png)
  *Automated data quality checks running on ingested data, ensuring integrity before analytics or extraction.*
- MeSh network:
  ![Dagster asset dependencies](Screenshot%202026-05-20%20at%2012.45.12.png)
  *Visualization of asset dependencies, showing how ingestion, extraction, and analytics assets are orchestrated.*
- Research geography:
  ![Dagster asset run success](Screenshot%202026-05-20%20at%2012.45.39.png)
  *A successful asset materialization run, with all steps completed and data available for downstream analytics.*
- Treatment outcome matrix:
  ![Dagster asset run error](Screenshot%202026-05-20%20at%2012.45.51.png)
- Population profile
  ![Dagster asset run warning](Screenshot%202026-05-20%20at%2012.45.58.png)
  *A run with warnings, such as partial data ingestion or recoverable issues, highlighted for review.*
- Funding landscape
  ![Dagster asset run info](Screenshot%202026-05-20%20at%2012.46.23.png)
  *Asset run metadata and logs, providing transparency into pipeline execution and data lineage.*

### Example: LLM Extraction Rate Limit and Long Run

![LLM extraction asset run taking over 10 hours and failing due to Gemini API rate limits](Screenshot%202026-05-20%20at%2012.31.59.png)
*The `extracted_treatment_outcomes` asset can take over 10 hours or fail due to Gemini API free-tier rate limits (20 requests/day). This is an external limitation, not a pipeline bug. See the [Gemini API quota documentation](https://ai.google.dev/gemini-api/docs/rate-limits) for more details.*



## Continuous Integration & Quality Checks

This project uses GitHub Actions for continuous integration (CI) to ensure code quality and reliability. On every push and pull request to `main`, the following checks are automatically run:

- **Linting:** Enforced with [Ruff](https://github.com/astral-sh/ruff) to maintain consistent code style.
- **Type Checking:** Enforced with [mypy](http://mypy-lang.org/) to catch type errors early.
- **Testing:** All unit and integration tests are run with [pytest](https://docs.pytest.org/).
- **Data Quality Checks:** Dagster asset checks are executed to validate data integrity and pipeline health.

You can find the workflow definition in `.github/workflows/ci.yml`.

### Running Checks Locally

To run the same checks locally before pushing:

```bash
# Linting
ruff check src/ tests/

# Type checking
mypy src/ tests/

# Run tests
pytest

# Run Dagster data quality checks
python src/dagster_pipeline/checks.py
```





