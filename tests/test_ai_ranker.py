"""Tests for core.ai_ranker module."""

import pandas as pd

from core.ai_ranker import score_results


def _sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "purchase_number": ["001", "002", "003"],
            "title": ["Ноутбук Dell", "Принтер HP", "Сервер IBM"],
            "url": [
                "https://example.com/1",
                "https://example.com/2",
                "https://example.com/3",
            ],
            "price": [50_000.0, 20_000.0, 300_000.0],
            "publish_date": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "source": ["docSearch", "extendedsearch", "docSearch"],
        }
    )


def test_score_results_adds_ai_score_column():
    df = _sample_df()
    result = score_results(df, query="ноутбук")
    assert "ai_score" in result.columns


def test_score_results_scores_between_0_and_1():
    df = _sample_df()
    result = score_results(df, query="ноутбук")
    assert result["ai_score"].between(0.0, 1.0).all()


def test_score_results_zero_threshold_keeps_all_rows():
    df = _sample_df()
    result = score_results(df, query="ноутбук", threshold=0.0)
    assert len(result) == len(df)


def test_score_results_high_threshold_filters_rows():
    df = _sample_df()
    # Current stub gives ai_score=1.0 for all rows; threshold >1 drops everything
    result = score_results(df, query="ноутбук", threshold=1.1)
    assert len(result) == 0


def test_score_results_does_not_modify_original_df():
    df = _sample_df()
    _ = score_results(df, query="ноутбук")
    assert "ai_score" not in df.columns
