from __future__ import annotations

from decimal import Decimal, InvalidOperation
from pathlib import Path


def parse_expenses_file(file_path: str | Path) -> list[dict[str, str | Decimal]]:
    """
    Parse an expenses file with lines in either of these forms:

        18.50//Milk
        7.20//Cleaning spray
        12

    Blank lines are ignored.

    Returns a list of dicts like:
        [{"amount": Decimal("18.50"), "description": "Milk"}, ...]
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Expenses file not found: {path}")

    expenses: list[dict[str, str | Decimal]] = []

    with path.open("r", encoding="utf-8") as f:
        for line_number, raw_line in enumerate(f, start=1):
            line = raw_line.strip()

            if not line:
                continue

            if "//" in line:
                amount_part, description_part = line.split("//", 1)
                amount_text = amount_part.strip()
                description = description_part.strip()
            else:
                amount_text = line
                description = ""

            try:
                amount = Decimal(amount_text)
            except InvalidOperation as exc:
                raise ValueError(
                    f"Invalid amount on line {line_number}: {amount_text!r}"
                ) from exc

            if amount < 0:
                raise ValueError(
                    f"Negative amounts are not allowed on line {line_number}: {amount}"
                )

            expenses.append({
                "amount": amount,
                "description": description,
            })

    return expenses
