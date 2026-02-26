"""Export a DataFrame to an Excel file (XLSX) as bytes."""

import io
import json

import pandas as pd


def to_excel_bytes(df: pd.DataFrame) -> bytes:
    """Serialize *df* to an Excel workbook and return the raw bytes.

    Args:
        df: The DataFrame to export.

    Returns:
        XLSX file content as :class:`bytes`, suitable for writing to disk or
        attaching to an e-mail.
    """
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Результаты")
    return buffer.getvalue()


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    """Serialize *df* to CSV (UTF-8 with BOM) and return bytes."""
    csv_text = df.to_csv(index=False)
    return csv_text.encode("utf-8-sig")


def to_txt_bytes(df: pd.DataFrame) -> bytes:
    """Serialize *df* to plain text table and return bytes."""
    txt = df.to_string(index=False)
    return txt.encode("utf-8")


def to_json_bytes(df: pd.DataFrame) -> bytes:
    """Serialize *df* to JSON and return bytes."""
    payload = df.to_dict(orient="records")
    return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
