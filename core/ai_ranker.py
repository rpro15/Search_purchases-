"""AI relevance ranker for search results.

Primary strategy uses ``sentence-transformers`` embeddings.
If model loading fails (e.g. offline environment), the ranker falls back to
token-overlap similarity so the feature remains usable.
"""

from __future__ import annotations

import math
import re
from functools import lru_cache

import pandas as pd

AI_MODELS = {
    "fast": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    "balanced": "intfloat/multilingual-e5-base",
    "quality": "BAAI/bge-m3",
}
DEFAULT_MODE = "balanced"


@lru_cache(maxsize=1)
def _get_model(model_name: str):
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name)


def _resolve_model(mode: str, model_name: str | None) -> str:
    if model_name:
        return model_name
    return AI_MODELS.get(mode, AI_MODELS[DEFAULT_MODE])


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower())


def _fallback_token_score(query: str, title: str) -> float:
    query_tokens = set(re.findall(r"[\w\-]+", _normalize_text(query), flags=re.UNICODE))
    title_tokens = set(re.findall(r"[\w\-]+", _normalize_text(title), flags=re.UNICODE))
    if not query_tokens or not title_tokens:
        return 0.0
    overlap = len(query_tokens & title_tokens)
    union = len(query_tokens | title_tokens)
    return overlap / union if union else 0.0


def _prepare_texts_for_model(
    query: str,
    titles: list[str],
    model_name: str,
) -> tuple[str, list[str]]:
    lowered = model_name.lower()
    if "e5" in lowered:
        query_text = f"query: {query}"
        title_texts = [f"passage: {title}" for title in titles]
        return query_text, title_texts
    return query, titles


def _embed_scores(query: str, titles: list[str], model_name: str) -> list[float]:
    from sentence_transformers import util

    model = _get_model(model_name)
    query_text, title_texts = _prepare_texts_for_model(query, titles, model_name)
    query_vec = model.encode([query_text], normalize_embeddings=True)
    title_vecs = model.encode(title_texts, normalize_embeddings=True)
    sims = util.cos_sim(query_vec, title_vecs)[0].tolist()
    return [max(0.0, min(1.0, (float(score) + 1.0) / 2.0)) for score in sims]


def score_results(
    df: pd.DataFrame,
    query: str,
    threshold: float = 0.0,
    mode: str = DEFAULT_MODE,
    model_name: str | None = None,
    allow_model_download: bool = False,
) -> pd.DataFrame:
    """Assign an AI relevance score to each row in *df*.

    Args:
        df: DataFrame of merged search results.
        query: The original search query string.
        threshold: Minimum score to keep a row (0.0 keeps all rows).
        mode: Ranking profile (``fast`` | ``balanced`` | ``quality``).
        model_name: Optional direct model override.
        allow_model_download: Allow downloading model weights if absent locally.

    Returns:
        DataFrame with an additional ``ai_score`` column (float 0–1).
        Rows with ``ai_score < threshold`` are dropped.
    """
    df = df.copy()

    if df.empty:
        df["ai_score"] = pd.Series(dtype="float64")
        return df

    titles = [str(value) for value in df.get("title", pd.Series([""] * len(df))).tolist()]
    resolved_model = _resolve_model(mode=mode, model_name=model_name)

    if allow_model_download:
        try:
            scores = _embed_scores(query=query, titles=titles, model_name=resolved_model)
        except Exception:
            scores = [_fallback_token_score(query=query, title=title) for title in titles]
    else:
        scores = [_fallback_token_score(query=query, title=title) for title in titles]

    df["ai_score"] = [float(score) if not math.isnan(float(score)) else 0.0 for score in scores]
    df = df.sort_values(by="ai_score", ascending=False)

    if threshold > 0.0:
        df = df[df["ai_score"] >= threshold]

    return df.reset_index(drop=True)
