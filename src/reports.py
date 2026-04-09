from __future__ import annotations

from decimal import Decimal
from typing import Any


def compute_day_summary(
    cash_in_report: Decimal,
    cash_in_till: Decimal,
    expenses: list[dict[str, Any]],
) -> dict[str, Decimal]:
    expenses_total = sum(
        Decimal(str(expense["amount"])) for expense in expenses
    )
    till_plus_expenses = cash_in_till + expenses_total
    difference = till_plus_expenses - cash_in_report

    return {
        "expenses_total": expenses_total,
        "till_plus_expenses": till_plus_expenses,
        "difference": difference,
    }
