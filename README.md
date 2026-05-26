# Endometriosis Treatment Evidence Pipeline — Solution


## Overview

This repository contains a fully reproducible, orchestrated pipeline for mapping the treatment evidence landscape for **endometriosis** using PubMed abstracts. The pipeline is built with Dagster, Docker Compose, and Streamlit, and demonstrates robust ingestion, analytics, and LLM-powered extraction (with clear limitations for free-tier LLMs).

## Architecture and Data Flow

![Architecture & Data Flow](assets/architecture.png)


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



**Query for Pipeline State Example:**
```sql
SELECT
     (SELECT COUNT(*) FROM pubmed_article) AS total_articles,
     (SELECT COUNT(*) FROM llm_extraction
           WHERE (extraction_error IS NULL OR extraction_error = '')
                AND treatment_outcomes IS NOT NULL
                AND treatment_outcomes::text != '[]') AS llm_extraction_success,
     (SELECT COUNT(*) FROM llm_extraction
           WHERE extraction_error IS NOT NULL AND extraction_error != '') AS llm_extraction_errors,
     (SELECT COUNT(*) FROM analytics_result) AS analytics_results;
```

| Table                    | Count |
|--------------------------|-------|
| pubmed_article           | 386   |
| llm_extraction (success) | 22    |
| llm_extraction (errors)  | 138   |
| analytics_result         | 4     |


**Query for Analytics Output Summary:**
```sql
SELECT
     -- Unique treatment-outcome pairs
     (SELECT COUNT(*) FROM (
          SELECT DISTINCT (treatment_outcome->>'treatment'), (treatment_outcome->>'outcome')
          FROM llm_extraction, jsonb_array_elements(treatment_outcomes) AS treatment_outcome
          WHERE (extraction_error IS NULL OR extraction_error = '')
               AND treatment_outcomes IS NOT NULL
               AND treatment_outcomes::text != '[]'
     ) AS unique_pairs) AS treatment_outcome_pairs,

     -- Years of data
     (SELECT (EXTRACT(YEAR FROM MAX(pub_date)) - EXTRACT(YEAR FROM MIN(pub_date)) + 1)
      FROM pubmed_article) AS years_of_data,

     -- MeSH co-occurrence pairs
     (SELECT jsonb_array_length(payload)
      FROM analytics_result
      WHERE name = 'mesh_cooccurrence_network') AS mesh_cooccurrence_pairs,

     -- Unique countries
     (SELECT COUNT(DISTINCT country)
      FROM pubmed_author
      WHERE country IS NOT NULL) AS unique_countries;
```

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

**Query for End-to-End Extraction Example:**
```sql
SELECT
     e.id,
     e.pubmed_id,
     a.title,
     a.journal,
     a.pub_date,
     e.treatments,
     e.outcomes,
     e.treatment_outcomes,
     e.study_design,
     e.population,
     e.extraction_confidence,
     e.extracted_ts
FROM llm_extraction e
JOIN pubmed_article a ON e.pubmed_id = a.pubmed_id
WHERE (e.extraction_error IS NULL OR e.extraction_error = '')
     AND e.treatment_outcomes IS NOT NULL
     AND e.treatment_outcomes::text != '[]'
ORDER BY e.id
LIMIT 3;
```

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

Below are the two key screenshots illustrating pipeline orchestration and LLM extraction limitations:

![LLM extraction asset run taking over 10 hours and failing due to Gemini API rate limits](assets/old/llm_extraction_failure.png)

*The `extracted_treatment_outcomes` asset can take over 10 hours or fail due to Gemini API free-tier rate limits (20 requests/day). This is an external limitation, not a pipeline bug. See the [Gemini API quota documentation](https://ai.google.dev/gemini-api/docs/rate-limits) for more details.*

![Dagster asset materialization](assets/old/dagster_asset_materialization.png)




## Dagster Asset Catalog: All Assets Materialized

Below is a screenshot of the Dagster asset catalog, showing that all pipeline assets are materialized. The results from these assets are visualized in the Streamlit dashboard screenshots below.

![Dagster Asset Catalog - All Assets Materialized](assets/materialized_assets.png)

---

## Streamlit Dashboard Analytics




Below are the main analytics pages available in the Streamlit dashboard, each with a corresponding screenshot:

1.1 Treatment-Outcome Matrix (with data)  
1.2 Treatment-Outcome Matrix (no data)  
2. Publication Trends  
3. MeSH Network  
4. Research Geography  
5. Knowledge Graph  
6. Population Profile  
7. Funding Landscape

Screenshots for each page are shown below.


### 1.1 Treatment-Outcome Matrix (with data)
![Treatment-Outcome Matrix with data](assets/treatment_outcome.png)
_Shows the Treatment-Outcome Matrix fully populated with extracted analytics when the pipeline and LLM extraction have succeeded._


### 1.2 Treatment-Outcome Matrix (no data)
![Treatment-Outcome Matrix with no data](assets/old/treatment_outcome_no_data.png)
_Shows the dashboard state when no data is available—this occurs if the pipeline has not been run or if LLM extraction was not possible (e.g., due to quota limits)._ 


### 2. Publication Trends
![Publication Trends](assets/publication_trends.png)
_Shows the number and distribution of endometriosis-related publications over time, helping identify research activity and trends in the field._


### 3. MeSH Network
![MeSH Network](assets/mesh_network.png)
_Displays a network of co-occurring MeSH terms, revealing thematic clusters and connections within the literature._


### 4. Research Geography
![Research Geography](assets/research_geography.png)
_Maps the geographic distribution of studies, showing which countries or regions are most active in endometriosis research._


### 5. Knowledge Graph
![Knowledge Graph](assets/knowledge_graph.png)
_Visualizes relationships between treatments, outcomes, and other biomedical entities, enabling exploration of the evidence network for endometriosis._


### 6. Population Profile
![Population Profile](assets/population_profile.png)
_Summarizes the demographic and clinical characteristics of study populations, such as sex, age group, disease stage, and special populations, providing context for interpreting the evidence landscape._


### 7. Funding Landscape
![Funding Landscape](assets/funding_landscape.png)
_Analyzes funding sources and patterns, highlighting the organizations and grants supporting endometriosis research._


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

# Run Dagster data quality checks (including extra checks for duplicates, nulls, value ranges)
python src/dagster_pipeline/checks_run_extra.py
```
### Additional Data Quality Checks

The pipeline now includes extra data quality checks:

- **No duplicate PubMed IDs:** Ensures all `pubmed_article.pubmed_id` values are unique.
- **No null titles:** Ensures all articles have a non-null title.
- **Extraction confidence in [0, 1]:** Ensures all `llm_extraction.extraction_confidence` values are between 0 and 1.

These checks are run alongside the existing checks for extraction failure rate and minimum article volume. All checks can be run locally with:

```bash
python src/dagster_pipeline/checks_run_extra.py
```

### CI/CD Validation Example

Below is a screenshot of the GitHub Actions CI/CD pipeline, showing successful and failed runs for data quality and code checks:

![CI/CD Actions Run Example](assets/old/ci_cd_actions_run_example.png)

**What is tested:**
- No duplicate PubMed IDs (`pubmed_article.pubmed_id` uniqueness)
- No null titles in articles
- Extraction confidence in [0, 1] for all LLM extractions
- Extraction failure rate below 20%
- Minimum article volume (at least 500)
- Linting (Ruff), type checking (mypy), and all tests (pytest)

These checks are enforced automatically on every push and pull request via GitHub Actions, ensuring robust data quality and code reliability.





