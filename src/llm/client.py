from __future__ import annotations

import json
import os
import time
from pathlib import Path

import litellm
from tenacity import retry, stop_after_attempt, wait_exponential

_PROMPT_DIR = Path(__file__).parent / "prompts"


def _load_prompt(name: str) -> str:
    return (_PROMPT_DIR / f"{name}.md").read_text()


TREATMENT_OUTCOME_PROMPT = _load_prompt("treatment_outcome")
MODEL = os.getenv("GEMINI_MODEL", "gemini/gemini-flash-latest")


@retry(stop=stop_after_attempt(1), wait=wait_exponential(multiplier=1, min=2, max=8))
def _call_llm(system_prompt: str, user_content: str) -> str:
    response = litellm.completion(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        temperature=0.0,
        response_format={"type": "json_object"},
    )
    return response.choices[0].message.content


def extract_treatment_outcomes_batch(
    abstracts: list[tuple[str, str]],
) -> list[dict]:
    results = []
    for pubmed_id, abstract in abstracts:
        for attempt in range(4):
            try:
                raw = _call_llm(TREATMENT_OUTCOME_PROMPT, abstract)
                data = json.loads(raw)
                data["pubmed_id"] = pubmed_id
                break
            except Exception as e:
                is_rate_limit = "RateLimitError" in str(e) or "429" in str(e)
                if is_rate_limit and attempt < 3:
                    wait = 30 * (attempt + 1)  # 30s, 60s, 90s
                    time.sleep(wait)
                    continue
                data = {
                    "pubmed_id": pubmed_id,
                    "treatments": [],
                    "outcomes": [],
                    "treatment_outcomes": [],
                    "study_design": "unknown",
                    "population": {},
                    "extraction_confidence": 0.0,
                    "extraction_error": str(e)[:200],
                }
                break
        results.append(data)
        time.sleep(2)  # reduced from 5s → 2s
    return results
