"""Tests for core.export_excel module."""

import pandas as pd

from core.export_excel import to_excel_bytes


def _sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "purchase_number": ["001", "002"],
            "title": ["Lot A", "Lot B"],
            "url": ["https://example.com/1", "https://example.com/2"],
            "price": [1000.0, 2000.0],
            "publish_date": ["2024-01-01", "2024-01-02"],
            "source": ["docSearch", "extendedsearch"],
        }
    )


def test_to_excel_bytes_returns_bytes():
    result = to_excel_bytes(_sample_df())
    assert isinstance(result, bytes)
    assert len(result) > 0


def test_to_excel_bytes_valid_xlsx():
    """Ensure the returned bytes can be read back as a valid Excel file."""
    import io

    df = _sample_df()
    xlsx_bytes = to_excel_bytes(df)
    result_df = pd.read_excel(io.BytesIO(xlsx_bytes), sheet_name="Результаты")
    assert list(result_df.columns) == list(df.columns)
    assert len(result_df) == len(df)


def test_to_excel_bytes_empty_df():
    """Exporting an empty DataFrame should not raise."""
    empty_df = pd.DataFrame(
        columns=["purchase_number", "title", "url", "price", "publish_date", "source"]
    )
    result = to_excel_bytes(empty_df)
    assert isinstance(result, bytes)
    assert len(result) > 0
