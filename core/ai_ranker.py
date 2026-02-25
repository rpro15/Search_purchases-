"""AI relevance ranker placeholder.

TODO: Replace the stub with a real implementation using sentence-transformers:
  1. Load a multilingual model, e.g. ``paraphrase-multilingual-MiniLM-L12-v2``.
  2. Encode the search query and each result title.
  3. Compute cosine similarity and store it in the ``ai_score`` column.
  4. Filter rows below ``threshold`` if desired.

Example (not yet active):
    from sentence_transformers import SentenceTransformer, util
    model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    query_emb = model.encode(query)
    title_embs = model.encode(df["title"].tolist())
    scores = util.cos_sim(query_emb, title_embs)[0].tolist()
"""

import pandas as pd


def score_results(
    df: pd.DataFrame,
    query: str,
    threshold: float = 0.0,
) -> pd.DataFrame:
    """Assign an AI relevance score to each row in *df*.

    Args:
        df: DataFrame of merged search results.
        query: The original search query string.
        threshold: Minimum score to keep a row (0.0 keeps all rows).

    Returns:
        DataFrame with an additional ``ai_score`` column (float 0–1).
        Rows with ``ai_score < threshold`` are dropped.
    """
    # TODO: replace with real sentence-transformers scoring (see module docstring)
    df = df.copy()
    df["ai_score"] = 1.0  # stub: give every result a perfect score

    if threshold > 0.0:
        df = df[df["ai_score"] >= threshold]

    return df.reset_index(drop=True)
