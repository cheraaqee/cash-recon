from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation

from db import (
    get_day_report,
    get_expenses_for_day,
    init_db,
    upsert_day_report,
)
from parser import parse_expenses_file
from reports import compute_day_summary
from utils import format_display_date, parse_iso_date, resolve_report_date


def non_negative_decimal(value: str) -> Decimal:
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise argparse.ArgumentTypeError(
            f"Invalid decimal value: {value!r}"
        ) from exc

    if result < 0:
        raise argparse.ArgumentTypeError(
            f"Negative values are not allowed: {value!r}"
        )

    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Cash reconciliation tool"
    )
    parser.add_argument(
        "--db-path",
        default="data/cash_recon.db",
        help="Path to SQLite database file",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser(
        "init-db",
        help="Initialize the SQLite database",
    )

    parse_expenses_cmd = subparsers.add_parser(
        "parse-expenses",
        help="Parse an expenses file and print the result",
    )
    parse_expenses_cmd.add_argument(
        "--expenses-file",
        required=True,
        help="Path to the expenses text file",
    )

    add_day_cmd = subparsers.add_parser(
        "add-day",
        help="Add or replace one day's report and expenses",
    )
    add_day_cmd.add_argument(
        "--date",
        help="Report date in YYYY-MM-DD format. Defaults to today.",
    )
    add_day_cmd.add_argument(
        "--cash-report",
        required=True,
        type=non_negative_decimal,
        help="Cash-in report amount",
    )
    add_day_cmd.add_argument(
        "--cash-till",
        required=True,
        type=non_negative_decimal,
        help="Cash physically in till",
    )
    add_day_cmd.add_argument(
        "--expenses-file",
        required=True,
        help="Path to the expenses text file",
    )

    show_day_cmd = subparsers.add_parser(
        "show-day",
        help="Show one day's report",
    )
    show_day_cmd.add_argument(
        "--date",
        required=True,
        help="Report date in YYYY-MM-DD format",
    )
    show_day_cmd.add_argument(
        "--include-expenses",
        action="store_true",
        help="Show the detailed expense list",
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "init-db":
        init_db(args.db_path)
        print(f"Initialized database at: {args.db_path}")
        return

    if args.command == "parse-expenses":
        expenses = parse_expenses_file(args.expenses_file)

        print("Parsed expenses:")
        for index, expense in enumerate(expenses, start=1):
            amount = expense["amount"]
            description = expense["description"]
            if description:
                print(f"{index:>2}. £{amount}  {description}")
            else:
                print(f"{index:>2}. £{amount}")
        return

    if args.command == "add-day":
        report_date = resolve_report_date(args.date)
        expenses = parse_expenses_file(args.expenses_file)

        upsert_day_report(
            report_date=report_date,
            cash_in_report=args.cash_report,
            cash_in_till=args.cash_till,
            expenses=expenses,
            db_path=args.db_path,
        )

        summary = compute_day_summary(
            cash_in_report=args.cash_report,
            cash_in_till=args.cash_till,
            expenses=expenses,
        )

        print(f"Saved report for: {report_date}")
        print(f"Cash-in report:   £{args.cash_report}")
        print(f"Cash in till:     £{args.cash_till}")
        print(f"Expenses total:   £{summary['expenses_total']}")
        print(f"Till + expenses:  £{summary['till_plus_expenses']}")
        print(f"Difference:       £{summary['difference']}")
        print(f"Expenses count:   {len(expenses)}")
        return

    if args.command == "show-day":
        report_date = parse_iso_date(args.date).isoformat()

        day_row = get_day_report(report_date, db_path=args.db_path)
        if day_row is None:
            print(f"No report found for date: {report_date}")
            return

        expense_rows = get_expenses_for_day(report_date, db_path=args.db_path)

        expenses = [
            {
                "amount": Decimal(row["amount"]),
                "description": row["description"],
            }
            for row in expense_rows
        ]

        summary = compute_day_summary(
            cash_in_report=Decimal(day_row["cash_in_report"]),
            cash_in_till=Decimal(day_row["cash_in_till"]),
            expenses=expenses,
        )

        print(f"DATE: {format_display_date(report_date)}")
        print()
        print(f"Cash-in report:   £{Decimal(day_row['cash_in_report'])}")
        print(f"Cash in till:     £{Decimal(day_row['cash_in_till'])}")
        print(f"Expenses total:   £{summary['expenses_total']}")
        print(f"Till + expenses:  £{summary['till_plus_expenses']}")
        print(f"Difference:       £{summary['difference']}")

        if args.include_expenses:
            print()
            print("Expenses:")
            if not expenses:
                print("  (none)")
            else:
                for index, expense in enumerate(expenses, start=1):
                    amount = expense["amount"]
                    description = str(expense["description"]).strip()
                    if description:
                        print(f"  {index:>2}. £{amount}  {description}")
                    else:
                        print(f"  {index:>2}. £{amount}")
        return


if __name__ == "__main__":
    main()
