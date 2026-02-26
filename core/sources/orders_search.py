"""Playwright-based scraper for zakupki.gov.ru extendedsearch (orders) results."""

from __future__ import annotations

import re
import time

import pandas as pd
from playwright.sync_api import TimeoutError as PlaywrightTimeout
from playwright.sync_api import sync_playwright

from core.settings import SearchSettings

BASE_URL = "https://zakupki.gov.ru/epz/order/extendedsearch/results.html"
PAGE_GOTO_TIMEOUT_MS = 90_000
PAGE_GOTO_RETRIES = 3

# Columns produced by this source
COLUMNS = ["purchase_number", "title", "url", "price", "publish_date", "source"]


def _parse_price(text: str) -> float | None:
    """Extract a numeric price from a string like '1 234 567,89 руб.'"""
    cleaned = re.sub(r"[^\d,.]", "", text.replace("\xa0", "").replace(" ", ""))
    cleaned = cleaned.replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return None


def _set_region(page, region: str) -> None:
    """Open the «Мой регион» modal and select the requested region."""
    try:
        page.click("a.region-change-link, button.region-change, #regionChangeLink", timeout=5_000)
        page.wait_for_selector(".modal-dialog, #regionModal, .modal.in", timeout=5_000)

        region_input = page.locator(
            "input[placeholder*='субъект'], input[placeholder*='регион'], "
            "#subjectRFFullName, input.region-input"
        ).first
        region_input.fill(region)
        time.sleep(1)

        page.click(
            ".tt-suggestion:first-child, .region-suggestion:first-child, "
            "li.ui-menu-item:first-child",
            timeout=5_000,
        )

        page.click(
            "button:has-text('Сохранить'), input[value='Сохранить'], "
            ".modal-footer button.btn-primary",
            timeout=5_000,
        )
        page.wait_for_load_state("networkidle", timeout=10_000)
    except PlaywrightTimeout:
        pass


def _open_results_page(page) -> None:
    """Open the source page with retries and clearer network diagnostics."""
    last_error: Exception | None = None
    for attempt in range(1, PAGE_GOTO_RETRIES + 1):
        try:
            page.goto(
                BASE_URL,
                timeout=PAGE_GOTO_TIMEOUT_MS,
                wait_until="commit",
            )
            return
        except PlaywrightTimeout as exc:
            last_error = exc
            if attempt < PAGE_GOTO_RETRIES:
                page.wait_for_timeout(2_000 * attempt)

    raise RuntimeError(
        "Не удалось открыть extendedsearch на zakupki.gov.ru: таймаут сети. "
        "Проверьте доступ к сайту из вашей сети/прокси/VPN и повторите попытку."
    ) from last_error


def _dismiss_blocking_modal(page) -> None:
    """Close or hide modal overlays that intercept clicks."""
    try:
        page.keyboard.press("Escape")
    except Exception:
        pass

    close_selectors = [
        "#modal-customer .close",
        "#modal-customer [data-dismiss='modal']",
        ".popupModalOverlay .close",
        ".modal .close",
    ]
    for selector in close_selectors:
        try:
            close_btn = page.locator(selector).first
            if close_btn.count() and close_btn.is_visible():
                close_btn.click(timeout=1_500)
                page.wait_for_timeout(200)
        except Exception:
            continue

    try:
        page.evaluate(
            """() => {
                const selectors = ['.popupModalOverlay', '#modal-customer', '.modal-backdrop'];
                for (const selector of selectors) {
                    document.querySelectorAll(selector).forEach((el) => {
                        if (el instanceof HTMLElement) {
                            el.style.pointerEvents = 'none';
                            el.style.display = 'none';
                            el.setAttribute('aria-hidden', 'true');
                        }
                    });
                }
            }"""
        )
    except Exception:
        pass


def search_orders(settings: SearchSettings) -> pd.DataFrame:
    """Scrape search results from the extendedsearch (orders) endpoint.

    Args:
        settings: Runtime search parameters.

    Returns:
        DataFrame with columns: purchase_number, title, url, price,
        publish_date, source.
    """
    rows: list[dict] = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )
        page = ctx.new_page()

        try:
            _open_results_page(page)
            _set_region(page, settings.region)

            # Fill in the search query
            search_input = page.locator(
                "input#searchString, input[name='searchString'], "
                "input[placeholder*='поиск'], input[type='search']"
            ).first
            search_input.fill(settings.query)

            # Apply date filters when available
            if settings.date_from:
                try:
                    page.fill(
                        "input#updateDateFrom, input[name='updateDateFrom']",
                        settings.date_from.strftime("%d.%m.%Y"),
                    )
                except Exception:
                    pass
            if settings.date_to:
                try:
                    page.fill(
                        "input#updateDateTo, input[name='updateDateTo']",
                        settings.date_to.strftime("%d.%m.%Y"),
                    )
                except Exception:
                    pass

            _dismiss_blocking_modal(page)
            search_button = page.locator(
                "button[type='submit'], input[type='submit'], "
                "button:has-text('Найти'), .search-btn"
            ).first
            try:
                search_button.click(timeout=10_000)
            except PlaywrightTimeout:
                _dismiss_blocking_modal(page)
                search_button.click(timeout=10_000, force=True)
            page.wait_for_load_state("networkidle", timeout=20_000)

            while len(rows) < settings.limit:
                page.wait_for_selector(
                    ".search-registry-entry-block, .registry-entry__form, "
                    "div.search-registry-entry",
                    timeout=15_000,
                )
                cards = page.locator(
                    ".search-registry-entry-block, .registry-entry__form, "
                    "div.search-registry-entry"
                ).all()

                for card in cards:
                    if len(rows) >= settings.limit:
                        break
                    try:
                        num_el = card.locator(
                            ".registry-entry__header-mid__number a, "
                            "a[href*='notice/'], a[href*='purchaseNumber']"
                        ).first
                        href = num_el.get_attribute("href") or ""
                        full_url = (
                            href if href.startswith("http")
                            else f"https://zakupki.gov.ru{href}"
                        )
                        purchase_number_match = re.search(
                            r"purchaseNumber=(\d+)|/(\d{19,})", href
                        )
                        purchase_number = (
                            purchase_number_match.group(1) or purchase_number_match.group(2)
                            if purchase_number_match else ""
                        )

                        title_el = card.locator(
                            ".registry-entry__body-value, .lot-name, "
                            ".search-result__name"
                        ).first
                        title = title_el.inner_text().strip()

                        price_el = card.locator(
                            ".price-block__cost, .registry-entry__body-value:has-text('руб')"
                        ).first
                        price_text = price_el.inner_text().strip() if price_el.count() else ""
                        price = _parse_price(price_text)

                        date_el = card.locator(
                            ".data-block__value:first-of-type, "
                            ".registry-entry__body-value:has-text('.')"
                        ).first
                        publish_date = date_el.inner_text().strip() if date_el.count() else ""

                        rows.append(
                            {
                                "purchase_number": purchase_number,
                                "title": title,
                                "url": full_url,
                                "price": price,
                                "publish_date": publish_date,
                                "source": "extendedsearch",
                            }
                        )
                    except Exception:
                        continue

                next_btn = page.locator(
                    "a.paginator-button.next, li.next a, a:has-text('Следующая')"
                ).first
                if next_btn.count() and next_btn.is_enabled():
                    next_btn.click()
                    page.wait_for_load_state("networkidle", timeout=15_000)
                else:
                    break

        except Exception as exc:
            raise RuntimeError(f"extendedsearch scraping failed: {exc}") from exc
        finally:
            browser.close()

    df = pd.DataFrame(rows, columns=COLUMNS) if rows else pd.DataFrame(columns=COLUMNS)
    return df[: settings.limit]
