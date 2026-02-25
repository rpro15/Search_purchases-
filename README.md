# Поиск закупок на zakupki.gov.ru

Инструмент для автоматизированного поиска закупок на портале [zakupki.gov.ru](https://zakupki.gov.ru) с выгрузкой результатов в Excel и опциональной отправкой по e-mail.

---

## Цель

Автоматически собирать данные о закупках из двух источников:

- **docSearch** — `https://zakupki.gov.ru/epz/order/docSearch/results.html`
- **extendedsearch** — `https://zakupki.gov.ru/epz/order/extendedsearch/results.html`

применять фильтр по региону через модальное окно «Мой регион» («Ваш субъект РФ» → Сохранить), объединять результаты, экспортировать в XLSX и при необходимости отправлять по e-mail.

---

## Быстрый старт (Windows)

### 1. Клонировать репозиторий

```bat
git clone https://github.com/rpro15/Search_purchases-.git
cd Search_purchases-
```

### 2. Создать виртуальное окружение и установить зависимости

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Установить браузер Playwright

```bat
playwright install chromium
```

### 4. Запустить приложение

```bat
streamlit run app.py
```

Браузер откроется автоматически по адресу `http://localhost:8501`.

---

## Структура проекта

```
app.py                  # Streamlit UI
requirements.txt
.gitignore
core/
  __init__.py
  settings.py           # Dataclass с параметрами поиска
  merge.py              # Объединение и дедупликация результатов
  ai_ranker.py          # AI-ранжирование (заглушка, TODO sentence-transformers)
  export_excel.py       # Экспорт DataFrame → XLSX
  email_mailru.py       # Отправка письма через SMTP mail.ru
  sources/
    __init__.py
    docsearch.py        # Заглушка для docSearch (TODO Playwright)
    orders_search.py    # Заглушка для extendedsearch (TODO Playwright)
```

---

## Использование UI

1. В боковой панели введите **поисковый запрос** и **регион** (по умолчанию `г Москва`).
2. Настройте диапазон дат, переключатели источников и лимит результатов.
3. При необходимости включите **AI-ранжирование** и задайте порог.
4. Для отправки по e-mail заполните поля SMTP (логин и пароль не сохраняются).
5. Нажмите **▶ Запустить поиск**.
6. Просмотрите таблицу результатов и скачайте Excel-файл.

---

## Дорожная карта (Roadmap)

- [ ] **Playwright-скрапинг docSearch**
  - Открыть `https://zakupki.gov.ru/epz/order/docSearch/results.html`
  - Выбрать регион через модальное окно «Мой регион» → «Ваш субъект РФ» → Сохранить
  - Ввести запрос, перебрать страницы до `limit` записей
  - Вернуть DataFrame (`purchase_number`, `title`, `url`, `price`, `publish_date`, `source`)

- [ ] **Playwright-скрапинг extendedsearch**
  - Аналогично для `https://zakupki.gov.ru/epz/order/extendedsearch/results.html`

- [ ] **Фильтрация по дате** — передавать `date_from` / `date_to` в запросы

- [ ] **AI-ранжирование** — реализовать `score_results` в `core/ai_ranker.py`
  с использованием `sentence-transformers` (модель `paraphrase-multilingual-MiniLM-L12-v2`)

- [ ] **Автоматический выбор региона** — Playwright-взаимодействие с полем «Ваш субъект РФ»

- [ ] **Тесты** — покрыть `merge.py`, `export_excel.py`, `ai_ranker.py`
