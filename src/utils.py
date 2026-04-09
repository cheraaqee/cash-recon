from __future__ import annotations

from datetime import date, datetime


def parse_iso_date(date_text: str) -> date:
    try:
        return datetime.strptime(date_text, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError(
            f"Invalid date: {date_text!r}. Expected format: YYYY-MM-DD"
        ) from exc


def resolve_report_date(date_text: str | None) -> str:
    """
    Return a date string in ISO format YYYY-MM-DD.

    If date_text is None, use today's local date.
    """
    if date_text is None:
        return date.today().isoformat()

    return parse_iso_date(date_text).isoformat()


def format_display_date(date_text: str) -> str:
    d = parse_iso_date(date_text)
    return d.strftime("%a %d %b %Y").upper()
