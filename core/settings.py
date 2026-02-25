"""Runtime configuration dataclasses for the search application."""

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class SearchSettings:
    """Parameters that control a single search run."""

    query: str
    region: str = "г Москва"
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    doc_search: bool = True
    extended_search: bool = True
    limit: int = 50
    ai_ranking: bool = False
    ai_threshold: float = 0.5

    # E-mail delivery (optional)
    email_recipient: str = ""
    smtp_login: str = ""
    smtp_password: str = ""
