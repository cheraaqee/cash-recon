from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
from pathlib import Path

from db import (
        get_day_report,
        get_expenses_for_day,
        get_expenses_in_range,
        get_reports_in_range,
        init_db,
        upsert_day_report,
        )
from parser import parse_expenses_file
from reports import (
        build_range_rows,
        compute_day_summary,
        generate_range_latex,
        write_range_csv
        )
from utils import (
        format_display_date,
        get_week_bounds,
        iter_date_strings,
        parse_iso_date,
        resolve_report_date,
        )


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


def fmt_money(value: Decimal) -> str:
    return f"{value:.2f}"


def load_range_rows(
        start_date: str,
        end_date: str,
        db_path: str,
        ) -> list[dict]:
    date_strings = iter_date_strings(start_date, end_date)

    report_rows = get_reports_in_range(start_date, end_date, db_path=db_path)
    expense_rows = get_expenses_in_range(start_date, end_date, db_path=db_path)

    reports_by_date = {
            row["report_date"]: {
                "cash_in_report": Decimal(row["cash_in_report"]),
                "cash_in_till": Decimal(row["cash_in_till"]),
                }
            for row in report_rows
            }

    expenses_by_date: dict[str, list[dict[str, str | Decimal]]] = {}
    for row in expense_rows:
        report_date = row["report_date"]
        expenses_by_date.setdefault(report_date, []).append(
                {
                    "amount": Decimal(row["amount"]),
                    "description": row["description"],
                    }
                )

    return build_range_rows(
            date_strings=date_strings,
            reports_by_date=reports_by_date,
            expenses_by_date=expenses_by_date,
            )


def print_range_rows(
        start_date: str,
        end_date: str,
        range_rows: list[dict],
        include_expenses: bool,
        label: str = "RANGE",
        ) -> None:
    print(
            f"{label}: {format_display_date(start_date)} — "
            f"{format_display_date(end_date)}"
            )
    print()
    print(
            f"{'DATE':<15} "
            f"{'CASH REP':>10} "
            f"{'CASH TILL':>10} "
            f"{'EXPENSES':>10} "
            f"{'TILL+EXP':>10} "
            f"{'DIFF':>10} "
            f"{'CUM REP':>10} "
            f"{'CUM TILL':>10} "
            f"{'CUM EXP':>10} "
            f"{'CUM T+E':>10} "
            f"{'CUM DIFF':>10}"
            )

    for row in range_rows:
        if row["has_data"]:
            print(
                    f"{format_display_date(row['date']):<15} "
                    f"{fmt_money(row['cash_in_report']):>10} "
                    f"{fmt_money(row['cash_in_till']):>10} "
                    f"{fmt_money(row['expenses_total']):>10} "
                    f"{fmt_money(row['till_plus_expenses']):>10} "
                    f"{fmt_money(row['difference']):>10} "
                    f"{fmt_money(row['cum_cash_in_report']):>10} "
                    f"{fmt_money(row['cum_cash_in_till']):>10} "
                    f"{fmt_money(row['cum_expenses_total']):>10} "
                    f"{fmt_money(row['cum_till_plus_expenses']):>10} "
                    f"{fmt_money(row['cum_difference']):>10}"
                    )
        else:
            print(
                    f"{format_display_date(row['date']):<15} "
                    f"{'-':>10} "
                    f"{'-':>10} "
                    f"{'-':>10} "
                    f"{'-':>10} "
                    f"{'-':>10} "
                    f"{fmt_money(row['cum_cash_in_report']):>10} "
                    f"{fmt_money(row['cum_cash_in_till']):>10} "
                    f"{fmt_money(row['cum_expenses_total']):>10} "
                    f"{fmt_money(row['cum_till_plus_expenses']):>10} "
                    f"{fmt_money(row['cum_difference']):>10}"
                    )

        if include_expenses and row["has_data"]:
            expenses = row["expenses"]
            if expenses:
                print("  Expenses:")
                for index, expense in enumerate(expenses, start=1):
                    amount = Decimal(str(expense["amount"]))
                    description = str(expense["description"]).strip()
                    if description:
                        print(f"    {index:>2}. £{amount}  {description}")
                    else:
                        print(f"    {index:>2}. £{amount}")


def write_text_file(path: str | Path, content: str) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


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

    show_range_cmd = subparsers.add_parser(
            "show-range",
            help="Show reports for a date range with cumulative totals",
            )
    show_range_cmd.add_argument(
            "--from",
            dest="date_from",
            required=True,
            help="Start date in YYYY-MM-DD format",
            )
    show_range_cmd.add_argument(
            "--to",
            dest="date_to",
            required=True,
            help="End date in YYYY-MM-DD format",
            )
    show_range_cmd.add_argument(
            "--include-expenses",
            action="store_true",
            help="Show the detailed expense list under each day",
            )

    show_week_cmd = subparsers.add_parser(
            "show-week",
            help="Show the full Monday-to-Sunday week for a given date",
            )
    show_week_cmd.add_argument(
            "--date",
            required=True,
            help="Any date within the target week, in YYYY-MM-DD format",
            )
    show_week_cmd.add_argument(
            "--include-expenses",
            action="store_true",
            help="Show the detailed expense list under each day",
            )

    show_week_to_date_cmd = subparsers.add_parser(
            "show-week-to-date",
            help="Show Monday up to the given date within the same week",
            )
    show_week_to_date_cmd.add_argument(
            "--date",
            help="End date in YYYY-MM-DD format. Defaults to today.",
            )
    show_week_to_date_cmd.add_argument(
            "--include-expenses",
            action="store_true",
            help="Show the detailed expense list under each day",
            )

    export_range_latex_cmd = subparsers.add_parser(
            "export-range-latex",
            help="Export a date range report as a LaTeX file",
            )
    export_range_latex_cmd.add_argument(
            "--from",
            dest="date_from",
            required=True,
            help="Start date in YYYY-MM-DD format",
            )
    export_range_latex_cmd.add_argument(
            "--to",
            dest="date_to",
            required=True,
            help="End date in YYYY-MM-DD format",
            )
    export_range_latex_cmd.add_argument(
            "--output",
            required=True,
            help="Output .tex file path",
            )
    export_range_latex_cmd.add_argument(
            "--include-expenses",
            action="store_true",
            help="Include detailed expenses in one cell per day",
            )
    export_range_latex_cmd.add_argument(
            "--title",
            default="Cash Reconciliation Report",
            help="Document title",
            )
    export_week_latex_cmd = subparsers.add_parser(
            "export-week-latex",
            help="Export the full Monday-to-Sunday week as a LaTeX file",
            )
    export_week_latex_cmd.add_argument(
            "--date",
            required=True,
            help="Any date within the target week (YYYY-MM-DD)",
            )
    export_week_latex_cmd.add_argument(
            "--output",
            required=True,
            help="Output .tex file path",
            )
    export_week_latex_cmd.add_argument(
            "--include-expenses",
            action="store_true",
            help="Include detailed expenses in one cell per day",
            )
    export_week_latex_cmd.add_argument(
            "--title",
            default="Weekly Cash Reconciliation Report",
            help="Document title",
            )

    export_week_to_date_latex_cmd = subparsers.add_parser(
            "export-week-to-date-latex",
            help="Export Monday up to the given date as a LaTeX file",
            )
    export_week_to_date_latex_cmd.add_argument(
            "--date",
            help="End date (YYYY-MM-DD). Defaults to today.",
            )
    export_week_to_date_latex_cmd.add_argument(
            "--output",
            required=True,
            help="Output .tex file path",
            )
    export_week_to_date_latex_cmd.add_argument(
            "--include-expenses",
            action="store_true",
            help="Include detailed expenses in one cell per day",
            )
    export_week_to_date_latex_cmd.add_argument(
            "--title",
            default="Week-to-Date Cash Reconciliation Report",
            help="Document title",
            )
    export_range_csv_cmd = subparsers.add_parser(
            "export-range-csv",
            help="Export a date range report as a CSV file",
            )
    export_range_csv_cmd.add_argument(
            "--from",
            dest="date_from",
            required=True,
            help="Start date in YYYY-MM-DD format",
            )
    export_range_csv_cmd.add_argument(
            "--to",
            dest="date_to",
            required=True,
            help="End date in YYYY-MM-DD format",
            )
    export_range_csv_cmd.add_argument(
            "--output",
            required=True,
            help="Output .csv file path",
            )
    export_range_csv_cmd.add_argument(
            "--include-expenses",
            action="store_true",
            help="Include expense details as a newline-separated field",
            )

    export_week_csv_cmd = subparsers.add_parser(
            "export-week-csv",
            help="Export the full Monday-to-Sunday week as a CSV file",
            )
    export_week_csv_cmd.add_argument(
            "--date",
            required=True,
            help="Any date within the target week (YYYY-MM-DD)",
            )
    export_week_csv_cmd.add_argument(
            "--output",
            required=True,
            help="Output .csv file path",
            )
    export_week_csv_cmd.add_argument(
            "--include-expenses",
            action="store_true",
            help="Include expense details as a newline-separated field",
            )

    export_week_to_date_csv_cmd = subparsers.add_parser(
            "export-week-to-date-csv",
            help="Export Monday up to the given date as a CSV file",
            )
    export_week_to_date_csv_cmd.add_argument(
            "--date",
            help="End date in YYYY-MM-DD format. Defaults to today.",
            )
    export_week_to_date_csv_cmd.add_argument(
            "--output",
            required=True,
            help="Output .csv file path",
            )
    export_week_to_date_csv_cmd.add_argument(
            "--include-expenses",
            action="store_true",
            help="Include expense details as a newline-separated field",
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

    if args.command == "show-range":
        start_date = parse_iso_date(args.date_from).isoformat()
        end_date = parse_iso_date(args.date_to).isoformat()

        range_rows = load_range_rows(
                start_date=start_date,
                end_date=end_date,
                db_path=args.db_path,
                )

        print_range_rows(
                start_date=start_date,
                end_date=end_date,
                range_rows=range_rows,
                include_expenses=args.include_expenses,
                label="RANGE",
                )
        return

    if args.command == "show-week":
        selected_date = parse_iso_date(args.date).isoformat()
        start_date, end_date = get_week_bounds(selected_date)

        range_rows = load_range_rows(
                start_date=start_date,
                end_date=end_date,
                db_path=args.db_path,
                )

        print_range_rows(
                start_date=start_date,
                end_date=end_date,
                range_rows=range_rows,
                include_expenses=args.include_expenses,
                label="WEEK",
                )
        return

    if args.command == "show-week-to-date":
        selected_date = resolve_report_date(args.date)
        start_date, _ = get_week_bounds(selected_date)
        end_date = selected_date

        range_rows = load_range_rows(
                start_date=start_date,
                end_date=end_date,
                db_path=args.db_path,
                )

        print_range_rows(
                start_date=start_date,
                end_date=end_date,
                range_rows=range_rows,
                include_expenses=args.include_expenses,
                label="WEEK-TO-DATE",
                )
        return

    if args.command == "export-range-latex":
        start_date = parse_iso_date(args.date_from).isoformat()
        end_date = parse_iso_date(args.date_to).isoformat()

        range_rows = load_range_rows(
                start_date=start_date,
                end_date=end_date,
                db_path=args.db_path,
                )

        latex_content = generate_range_latex(
                title=args.title,
                start_date_display=format_display_date(start_date),
                end_date_display=format_display_date(end_date),
                range_rows=range_rows,
                include_expenses=args.include_expenses,
                )

        write_text_file(args.output, latex_content)
        print(f"Wrote LaTeX report to: {args.output}")
        return
    if args.command == "export-week-latex":
        selected_date = parse_iso_date(args.date).isoformat()
        start_date, end_date = get_week_bounds(selected_date)

        range_rows = load_range_rows(
                start_date=start_date,
                end_date=end_date,
                db_path=args.db_path,
                )

        latex_content = generate_range_latex(
                title=args.title,
                start_date_display=format_display_date(start_date),
                end_date_display=format_display_date(end_date),
                range_rows=range_rows,
                include_expenses=args.include_expenses,
                )

        write_text_file(args.output, latex_content)
        print(f"Wrote LaTeX report to: {args.output}")
        return
    if args.command == "export-week-to-date-latex":
        selected_date = resolve_report_date(args.date)
        start_date, _ = get_week_bounds(selected_date)
        end_date = selected_date

        range_rows = load_range_rows(
                start_date=start_date,
                end_date=end_date,
                db_path=args.db_path,
                )

        latex_content = generate_range_latex(
                title=args.title,
                start_date_display=format_display_date(start_date),
                end_date_display=format_display_date(end_date),
                range_rows=range_rows,
                include_expenses=args.include_expenses,
                )

        write_text_file(args.output, latex_content)
        print(f"Wrote LaTeX report to: {args.output}")
        return
    if args.command == "export-range-csv":
        start_date = parse_iso_date(args.date_from).isoformat()
        end_date = parse_iso_date(args.date_to).isoformat()

        range_rows = load_range_rows(
                start_date=start_date,
                end_date=end_date,
                db_path=args.db_path,
                )

        write_range_csv(
                output_path=args.output,
                range_rows=range_rows,
                include_expenses=args.include_expenses,
                )

        print(f"Wrote CSV report to: {args.output}")
        return
    if args.command == "export-week-csv":
        selected_date = parse_iso_date(args.date).isoformat()
        start_date, end_date = get_week_bounds(selected_date)

        range_rows = load_range_rows(
                start_date=start_date,
                end_date=end_date,
                db_path=args.db_path,
                )

        write_range_csv(
                output_path=args.output,
                range_rows=range_rows,
                include_expenses=args.include_expenses,
                )

        print(f"Wrote CSV report to: {args.output}")
        return

    if args.command == "export-week-to-date-csv":
        selected_date = resolve_report_date(args.date)
        start_date, _ = get_week_bounds(selected_date)
        end_date = selected_date

        range_rows = load_range_rows(
                start_date=start_date,
                end_date=end_date,
                db_path=args.db_path,
                )

        write_range_csv(
                output_path=args.output,
                range_rows=range_rows,
                include_expenses=args.include_expenses,
                )

        print(f"Wrote CSV report to: {args.output}")
        return




if __name__ == "__main__":
    main()
