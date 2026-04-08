from __future__ import annotations

import argparse
from parser import parse_expenses_file
from db import init_db


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

    init_db_cmd = subparsers.add_parser(
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


if __name__ == "__main__":
    main()
