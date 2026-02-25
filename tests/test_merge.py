"""Tests for core.merge module."""

import pandas as pd
import pytest

from core.merge import merge_results


def _make_df(rows: list[dict]) -> pd.DataFrame:
    columns = ["purchase_number", "title", "url", "price", "publish_date", "source"]
    return pd.DataFrame(rows, columns=columns)


def test_merge_empty_list():
    result = merge_results([])
    assert result.empty


def test_merge_single_df():
    df = _make_df(
        [
            {
                "purchase_number": "001",
                "title": "Test",
                "url": "https://example.com",
                "price": 1000.0,
                "publish_date": "2024-01-01",
                "source": "docSearch",
            }
        ]
    )
    result = merge_results([df])
    assert len(result) == 1
    assert result.iloc[0]["purchase_number"] == "001"


def test_merge_deduplicates_by_purchase_number():
    df1 = _make_df(
        [
            {
                "purchase_number": "001",
                "title": "Lot A",
                "url": "https://example.com/1",
                "price": 1000.0,
                "publish_date": "2024-01-01",
                "source": "docSearch",
            }
        ]
    )
    df2 = _make_df(
        [
            {
                "purchase_number": "001",
                "title": "Lot A duplicate",
                "url": "https://example.com/1",
                "price": 1000.0,
                "publish_date": "2024-01-01",
                "source": "extendedsearch",
            },
            {
                "purchase_number": "002",
                "title": "Lot B",
                "url": "https://example.com/2",
                "price": 2000.0,
                "publish_date": "2024-01-02",
                "source": "extendedsearch",
            },
        ]
    )
    result = merge_results([df1, df2])
    assert len(result) == 2
    assert set(result["purchase_number"]) == {"001", "002"}


def test_merge_sorts_by_publish_date_descending():
    df = _make_df(
        [
            {
                "purchase_number": "001",
                "title": "Old",
                "url": "https://example.com/1",
                "price": 1000.0,
                "publish_date": "2024-01-01",
                "source": "docSearch",
            },
            {
                "purchase_number": "002",
                "title": "New",
                "url": "https://example.com/2",
                "price": 2000.0,
                "publish_date": "2024-06-01",
                "source": "docSearch",
            },
        ]
    )
    result = merge_results([df])
    assert result.iloc[0]["purchase_number"] == "002"
    assert result.iloc[1]["purchase_number"] == "001"


def test_merge_multiple_sources():
    df1 = _make_df(
        [
            {
                "purchase_number": "001",
                "title": "Lot 1",
                "url": "https://example.com/1",
                "price": 1000.0,
                "publish_date": "2024-01-01",
                "source": "docSearch",
            }
        ]
    )
    df2 = _make_df(
        [
            {
                "purchase_number": "002",
                "title": "Lot 2",
                "url": "https://example.com/2",
                "price": 2000.0,
                "publish_date": "2024-01-02",
                "source": "extendedsearch",
            }
        ]
    )
    result = merge_results([df1, df2])
    assert len(result) == 2
    sources = set(result["source"])
    assert "docSearch" in sources
    assert "extendedsearch" in sources
