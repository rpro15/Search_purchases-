"""Merge and deduplicate results from multiple search sources."""

import pandas as pd


def merge_results(dfs: list[pd.DataFrame]) -> pd.DataFrame:
    """Concatenate DataFrames and deduplicate by purchase_number or url.

    Args:
        dfs: List of DataFrames produced by individual source scrapers.
             Each must contain at least a ``purchase_number`` or ``url`` column.

    Returns:
        A single deduplicated DataFrame sorted by publish_date descending.
    """
    if not dfs:
        return pd.DataFrame()

    combined = pd.concat(dfs, ignore_index=True)

    # Deduplicate: prefer rows where purchase_number is non-empty/non-null.
    if "purchase_number" in combined.columns:
        combined = combined.drop_duplicates(subset=["purchase_number"], keep="first")
    elif "url" in combined.columns:
        combined = combined.drop_duplicates(subset=["url"], keep="first")

    if "publish_date" in combined.columns:
        combined = combined.sort_values("publish_date", ascending=False)

    return combined.reset_index(drop=True)
