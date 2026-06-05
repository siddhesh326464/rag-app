"""
Phase 2 — RAGAS + Tool Correctness metrics.

Key design decisions:
  - Judge LLM  : Groq llama-3.1-8b-instant via JUDGE_GROQ key (never touches prod key)
  - Embeddings : Vertex AI text-embedding-004 — same model as production, no PyTorch needed
  - Rate limits: GENERAL_BATCH_SIZE=1 + COOLDOWN_MINI between samples keeps each 60s window
                 well under Groq's 6,000 TPM on_demand ceiling.
  - Resilience : exponential backoff retry (up to 8 attempts, max 5 min wait) on any 429.
                 The pipeline will always complete — it just waits longer if rate-limited.
"""

import os
import pandas as pd
import asyncio
import logfire
import pandas as pd
from openai import AsyncOpenAI
from dotenv import load_dotenv
from langchain.embeddings import HuggingFaceEmbeddings

from ragas.llms import llm_factory
from ragas import SingleTurnSample
from ragas.metrics.collections import (
    Faithfulness,
    AnswerRelevancy,
    ContextPrecision,
    ContextRecall,
    AnswerCorrectness,
)

load_dotenv()


GROQ_BASE_URL  = "https://api.groq.com/openai/v1"
JUDGE_MODEL    = "llama-3.1-8b-instant"

COOLDOWN_STANDARD = 62
COOLDOWN_MINI     = 40
AC_BATCH_SIZE = 8


def build_judge():
    """
    Builds the Groq judge LLM instance using the JUDGE_GROQ API key.
    Returns:
        An instance of the Groq LLM configured for evaluation.
    """
    api_key = os.getenv("EVAL_API_KEY")
    client = AsyncOpenAI(base_url=GROQ_BASE_URL, api_key=api_key)
    llm = llm_factory(JUDGE_MODEL,client=client,provider="openai")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        use_api = False
        )
    return llm, embeddings


async def _cooldown(seconds: int, label: str, status_cb=None):
    msg = f"⏳ {seconds}s cooldown after {label} (Groq TPM buffer)..."
    if status_cb:
        status_cb(msg)
    for _ in range(seconds // 10):
        await asyncio.sleep(10)
    if status_cb:
        status_cb("✅ Ready — starting next experiment.")

def _prep_sample(golden_dataset:dict)->list:
    """
    Returns only samples with actual_response populated.
    Contexts are trimmed to CONTEXT_TRUNCATE chars and CONTEXT_LIMIT chunks
    to keep each RAGAS LLM call within the 6,000 TPM ceiling.
    """
    valid = []
    for s in golden_dataset["rag_samples"]:
        response = s.get("actual_response", "").strip()
        if not response:
            continue
        contexts = s.get("actual_contexts") or s.get("relevant_contexts") or []
        valid.append({**s, "actual_contexts": contexts})
    return valid

def score_df(metric_key: str, samples: list, scores: list) -> pd.DataFrame:
    return pd.DataFrame([
        {"question": s["question"][:65], metric_key: round(float(r.value), 3)}
        for s, r in zip(samples, scores)
    ])