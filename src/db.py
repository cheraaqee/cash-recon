from __future__ import annotations

import sqlite3
from decimal import Decimal
from pathlib import Path

DEFAULT_DB_PATH = Path("data/cash_recon.db")


def get_connection(db_path: str | Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: str | Path = DEFAULT_DB_PATH) -> None:
    with get_connection(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS daily_reports (
                report_date TEXT PRIMARY KEY,
                cash_in_report TEXT NOT NULL,
                cash_in_till TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_date TEXT NOT NULL,
                amount TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (report_date) REFERENCES daily_reports(report_date)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_expenses_report_date
            ON expenses(report_date);
            """
        )


def upsert_day_report(
    report_date: str,
    cash_in_report: Decimal,
    cash_in_till: Decimal,
    expenses: list[dict[str, str | Decimal]],
    db_path: str | Path = DEFAULT_DB_PATH,
) -> None:
    with get_connection(db_path) as conn:
        conn.execute(
            """
            INSERT INTO daily_reports (
                report_date,
                cash_in_report,
                cash_in_till
            )
            VALUES (?, ?, ?)
            ON CONFLICT(report_date) DO UPDATE SET
                cash_in_report = excluded.cash_in_report,
                cash_in_till = excluded.cash_in_till,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                report_date,
                str(cash_in_report),
                str(cash_in_till),
            ),
        )

        conn.execute(
            "DELETE FROM expenses WHERE report_date = ?",
            (report_date,),
        )

        conn.executemany(
            """
            INSERT INTO expenses (
                report_date,
                amount,
                description
            )
            VALUES (?, ?, ?)
            """,
            [
                (
                    report_date,
                    str(expense["amount"]),
                    str(expense["description"]),
                )
                for expense in expenses
            ],
        )
