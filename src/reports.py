from __future__ import annotations

from decimal import Decimal
from typing import Any


ZERO = Decimal("0")


def compute_day_summary(
    cash_in_report: Decimal,
    cash_in_till: Decimal,
    expenses: list[dict[str, Any]],
) -> dict[str, Decimal]:
    expenses_total = sum(
        (Decimal(str(expense["amount"])) for expense in expenses),
        start=ZERO,
    )
    till_plus_expenses = cash_in_till + expenses_total
    difference = till_plus_expenses - cash_in_report

    return {
        "expenses_total": expenses_total,
        "till_plus_expenses": till_plus_expenses,
        "difference": difference,
    }


def build_range_rows(
    date_strings: list[str],
    reports_by_date: dict[str, dict[str, Decimal]],
    expenses_by_date: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    cumulative_cash_report = ZERO
    cumulative_cash_till = ZERO
    cumulative_expenses = ZERO
    cumulative_till_plus_expenses = ZERO
    cumulative_difference = ZERO

    rows: list[dict[str, Any]] = []

    for date_text in date_strings:
        report = reports_by_date.get(date_text)
        expenses = expenses_by_date.get(date_text, [])

        if report is None:
            day_cash_report = ZERO
            day_cash_till = ZERO
            summary = {
                "expenses_total": ZERO,
                "till_plus_expenses": ZERO,
                "difference": ZERO,
            }
            has_data = False
        else:
            day_cash_report = report["cash_in_report"]
            day_cash_till = report["cash_in_till"]
            summary = compute_day_summary(
                cash_in_report=day_cash_report,
                cash_in_till=day_cash_till,
                expenses=expenses,
            )
            has_data = True

        cumulative_cash_report += day_cash_report
        cumulative_cash_till += day_cash_till
        cumulative_expenses += summary["expenses_total"]
        cumulative_till_plus_expenses += summary["till_plus_expenses"]
        cumulative_difference += summary["difference"]

        rows.append(
            {
                "date": date_text,
                "has_data": has_data,
                "cash_in_report": day_cash_report,
                "cash_in_till": day_cash_till,
                "expenses_total": summary["expenses_total"],
                "till_plus_expenses": summary["till_plus_expenses"],
                "difference": summary["difference"],
                "cum_cash_in_report": cumulative_cash_report,
                "cum_cash_in_till": cumulative_cash_till,
                "cum_expenses_total": cumulative_expenses,
                "cum_till_plus_expenses": cumulative_till_plus_expenses,
                "cum_difference": cumulative_difference,
                "expenses": expenses,
            }
        )

    return rows
