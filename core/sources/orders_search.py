"""Stub scraper for zakupki.gov.ru extendedsearch (orders) results.

TODO: Replace the stub with a real Playwright-based scraper that:
  1. Opens https://zakupki.gov.ru/epz/order/extendedsearch/results.html
  2. Sets the region via the "Мой регион" modal
     ("Ваш субъект РФ" field → select region → Save).
  3. Enters the search query and paginates through results up to `limit`.
  4. Extracts purchase_number, title, url, price, publish_date and returns a DataFrame.
"""

import pandas as pd

from core.settings import SearchSettings

# Columns produced by this source
COLUMNS = ["purchase_number", "title", "url", "price", "publish_date", "source"]


def search_orders(settings: SearchSettings) -> pd.DataFrame:
    """Return stub search results from the extendedsearch (orders) endpoint.

    Args:
        settings: Runtime search parameters.

    Returns:
        DataFrame with columns: purchase_number, title, url, price,
        publish_date, source.
    """
    # TODO: implement Playwright scraping for
    # https://zakupki.gov.ru/epz/order/extendedsearch/results.html
    stub_rows = [
        {
            "purchase_number": "0000000000000000003",
            "title": f"[orders stub] {settings.query} — заказ 1",
            "url": "https://zakupki.gov.ru/epz/order/extendedsearch/results.html",
            "price": 50_000.0,
            "publish_date": "2024-01-03",
            "source": "extendedsearch",
        },
        {
            "purchase_number": "0000000000000000004",
            "title": f"[orders stub] {settings.query} — заказ 2",
            "url": "https://zakupki.gov.ru/epz/order/extendedsearch/results.html",
            "price": 75_000.0,
            "publish_date": "2024-01-04",
            "source": "extendedsearch",
        },
    ]
    return pd.DataFrame(stub_rows, columns=COLUMNS)[: settings.limit]
