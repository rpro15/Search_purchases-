"""Export a DataFrame to an Excel file (XLSX) as bytes."""

import io

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
