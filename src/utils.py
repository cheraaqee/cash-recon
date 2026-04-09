from __future__ import annotations

from datetime import date, datetime, timedelta


def parse_iso_date(date_text: str) -> date:
    try:
        return datetime.strptime(date_text, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError(
            f"Invalid date: {date_text!r}. Expected format: YYYY-MM-DD"
        ) from exc


def resolve_report_date(date_text: str | None) -> str:
    if date_text is None:
        return date.today().isoformat()

    return parse_iso_date(date_text).isoformat()


def format_display_date(date_text: str) -> str:
    d = parse_iso_date(date_text)
    return d.strftime("%a %d %b %Y").upper()


def iter_date_strings(start_date_text: str, end_date_text: str) -> list[str]:
    start_date = parse_iso_date(start_date_text)
    end_date = parse_iso_date(end_date_text)

    if start_date > end_date:
        raise ValueError(
            f"Start date {start_date_text} cannot be after end date {end_date_text}"
        )

    dates: list[str] = []
    current = start_date
    while current <= end_date:
        dates.append(current.isoformat())
        current += timedelta(days=1)

    return dates


def get_week_bounds(date_text: str) -> tuple[str, str]:
    d = parse_iso_date(date_text)
    monday = d - timedelta(days=d.weekday())
    sunday = monday + timedelta(days=6)
    return monday.isoformat(), sunday.isoformat()
