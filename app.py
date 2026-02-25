"""Streamlit UI for the zakupki.gov.ru purchase search tool."""

import datetime

import pandas as pd
import streamlit as st

from core.ai_ranker import score_results
from core.email_mailru import send_email
from core.export_excel import to_excel_bytes
from core.merge import merge_results
from core.settings import SearchSettings
from core.sources.docsearch import search_docsearch
from core.sources.orders_search import search_orders

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Поиск закупок",
    page_icon="🔍",
    layout="wide",
)

st.title("🔍 Поиск закупок на zakupki.gov.ru")

# ---------------------------------------------------------------------------
# Sidebar — search parameters
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Параметры поиска")

    query = st.text_input("Поисковый запрос", value="")

    region = st.text_input(
        "Регион",
        value="г Москва",
        help="Введите регион в текстовом виде. "
        "TODO: автоматический выбор через Playwright (модальное окно «Мой регион»).",
    )

    st.subheader("Диапазон дат")
    date_from = st.date_input(
        "Дата с",
        value=datetime.date.today() - datetime.timedelta(days=30),
    )
    date_to = st.date_input("Дата по", value=datetime.date.today())
    # TODO: wire date_from / date_to to the Playwright scrapers once implemented

    st.subheader("Источники")
    doc_search = st.checkbox("Поиск в документах (docSearch)", value=True)
    extended_search = st.checkbox("Поиск в заказах (extendedsearch)", value=True)

    limit = st.number_input(
        "Лимит результатов на источник",
        min_value=1,
        max_value=500,
        value=50,
        step=10,
    )

    st.subheader("AI-ранжирование (опционально)")
    ai_ranking = st.checkbox("Включить AI-ранжирование", value=False)
    ai_threshold = st.slider(
        "Порог релевантности",
        min_value=0.0,
        max_value=1.0,
        value=0.5,
        step=0.05,
        disabled=not ai_ranking,
        help="TODO: будет использоваться sentence-transformers для расчёта схожести.",
    )

    st.subheader("Отправка по e-mail (опционально)")
    email_recipient = st.text_input("Получатель (e-mail)", value="")
    email_mode = st.radio(
        "Режим отправки",
        options=["mailto", "smtp"],
        format_func=lambda m: "📬 Открыть почтовый клиент (без пароля)"
        if m == "mailto"
        else "📤 SMTP (mail.ru, с паролем)",
        index=0,
        help="mailto — создаёт ссылку для вашего почтового клиента. "
        "SMTP — отправляет письмо с вложением автоматически.",
    )
    smtp_login = ""
    smtp_password = ""
    if email_mode == "smtp":
        smtp_login = st.text_input("SMTP логин (mail.ru)", value="")
        smtp_password = st.text_input(
            "SMTP пароль",
            value="",
            type="password",
            help="Используйте пароль приложения. Данные не сохраняются.",
        )

# ---------------------------------------------------------------------------
# Main area — run search
# ---------------------------------------------------------------------------
run_clicked = st.button("▶ Запустить поиск", type="primary", disabled=not query)

if not query:
    st.info("Введите поисковый запрос в боковой панели и нажмите «Запустить поиск».")

if run_clicked and query:
    settings = SearchSettings(
        query=query,
        region=region,
        date_from=date_from,
        date_to=date_to,
        doc_search=doc_search,
        extended_search=extended_search,
        limit=int(limit),
        ai_ranking=ai_ranking,
        ai_threshold=float(ai_threshold),
        email_recipient=email_recipient,
        email_mode=email_mode,
        smtp_login=smtp_login,
        smtp_password=smtp_password,
    )

    results_dfs: list[pd.DataFrame] = []

    with st.spinner("Выполняется поиск…"):
        if settings.doc_search:
            df_doc = search_docsearch(settings)
            results_dfs.append(df_doc)

        if settings.extended_search:
            df_orders = search_orders(settings)
            results_dfs.append(df_orders)

    combined = merge_results(results_dfs)

    if settings.ai_ranking and not combined.empty:
        with st.spinner("AI-ранжирование…"):
            combined = score_results(
                combined,
                query=settings.query,
                threshold=settings.ai_threshold,
            )

    st.session_state["results"] = combined
    st.session_state["settings"] = settings

# ---------------------------------------------------------------------------
# Display results
# ---------------------------------------------------------------------------
if "results" in st.session_state:
    combined: pd.DataFrame = st.session_state["results"]
    settings: SearchSettings = st.session_state["settings"]

    if combined.empty:
        st.warning("Результаты не найдены.")
    else:
        st.success(f"Найдено записей: {len(combined)}")
        st.dataframe(combined, use_container_width=True)

        # ----------------------------------------------------------------
        # Excel download
        # ----------------------------------------------------------------
        xlsx_bytes = to_excel_bytes(combined)
        st.download_button(
            label="⬇ Скачать Excel",
            data=xlsx_bytes,
            file_name="results.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        # ----------------------------------------------------------------
        # E-mail sending
        # ----------------------------------------------------------------
        if settings.email_recipient:
            if settings.email_mode == "mailto":
                import urllib.parse

                subject = urllib.parse.quote(
                    f"Результаты поиска закупок: {settings.query}"
                )
                body = urllib.parse.quote(
                    f"Поисковый запрос: {settings.query}\n"
                    f"Регион: {settings.region}\n"
                    f"Записей: {len(combined)}\n\n"
                    "Файл results.xlsx прикреплён вручную."
                )
                mailto_url = (
                    f"mailto:{settings.email_recipient}"
                    f"?subject={subject}&body={body}"
                )
                st.markdown(
                    f'<a href="{mailto_url}" target="_blank">'
                    "📬 Открыть письмо в почтовом клиенте</a>",
                    unsafe_allow_html=True,
                )
                st.caption(
                    "Скачайте Excel-файл выше и прикрепите его к письму вручную. "
                    "Автоматическое прикрепление через mailto: не поддерживается браузерами."
                )
            else:
                email_fields_filled = all(
                    [settings.smtp_login, settings.smtp_password]
                )
                if email_fields_filled:
                    if st.button("📧 Отправить по e-mail (SMTP)"):
                        try:
                            send_email(
                                recipient=settings.email_recipient,
                                subject=f"Результаты поиска закупок: {settings.query}",
                                body=(
                                    f"Поисковый запрос: {settings.query}\n"
                                    f"Регион: {settings.region}\n"
                                    f"Записей: {len(combined)}\n"
                                ),
                                attachment_bytes=xlsx_bytes,
                                attachment_filename="results.xlsx",
                                smtp_login=settings.smtp_login,
                                smtp_password=settings.smtp_password,
                            )
                            st.success("Письмо успешно отправлено!")
                        except Exception as exc:
                            st.error(f"Ошибка отправки: {exc}")
                else:
                    st.caption(
                        "Заполните SMTP логин и пароль в боковой панели для отправки."
                    )
        else:
            st.caption(
                "Укажите e-mail получателя в боковой панели для отправки результатов."
            )
