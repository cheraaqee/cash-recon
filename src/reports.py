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


def latex_escape(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }

    escaped = []
    for char in text:
        escaped.append(replacements.get(char, char))
    return "".join(escaped)


def format_money(value: Decimal) -> str:
    return f"{value:.2f}"


def build_expenses_cell(expenses: list[dict[str, Any]]) -> str:
    if not expenses:
        return ""

    lines: list[str] = []
    for expense in expenses:
        amount = format_money(Decimal(str(expense["amount"])))
        description = str(expense["description"]).strip()

        if description:
            lines.append(rf"\pounds {amount} -- {latex_escape(description)}")
        else:
            lines.append(rf"\pounds {amount}")

    joined_lines = r" \\ ".join(lines)
    return rf"\makecell[l]{{{joined_lines}}}"

def generate_range_latex(
    title: str,
    start_date_display: str,
    end_date_display: str,
    range_rows: list[dict[str, Any]],
    include_expenses: bool = False,
) -> str:
    if include_expenses:
        column_spec = (
            r"p{3.2cm} r r r r r| r r r r r p{5.8cm}"
        )
        header = (
            r"Date & Cash Rep & Cash Till & Expenses & Till+Exp & Diff & "
            r"Cum Rep & Cum Till & Cum Exp & Cum T+E & Cum Diff & Expense Details \\"
        )
    else:
        column_spec = r"p{3.2cm} r r r r r r r r r r"
        header = (
            r"Date & Cash Rep & Cash Till & Expenses & Till+Exp & Diff & "
            r"Cum Rep & Cum Till & Cum Exp & Cum T+E & Cum Diff \\"
        )

    body_lines: list[str] = []

    for row in range_rows:
        if row["has_data"]:
            values = [
                latex_escape(row["date"]),
                format_money(row["cash_in_report"]),
                format_money(row["cash_in_till"]),
                format_money(row["expenses_total"]),
                format_money(row["till_plus_expenses"]),
                format_money(row["difference"]),
                format_money(row["cum_cash_in_report"]),
                format_money(row["cum_cash_in_till"]),
                format_money(row["cum_expenses_total"]),
                format_money(row["cum_till_plus_expenses"]),
                format_money(row["cum_difference"]),
            ]
        else:
            values = [
                latex_escape(row["date"]),
                "-",
                "-",
                "-",
                "-",
                "-",
                format_money(row["cum_cash_in_report"]),
                format_money(row["cum_cash_in_till"]),
                format_money(row["cum_expenses_total"]),
                format_money(row["cum_till_plus_expenses"]),
                format_money(row["cum_difference"]),
            ]

        if include_expenses:
            expense_cell = build_expenses_cell(row["expenses"]) if row["has_data"] else ""
            values.append(expense_cell)

        line = " & ".join(values) + r" \\ \hline"
        body_lines.append(line)

    body = "\n".join(body_lines)

    latex = rf"""
\documentclass[11pt]{{article}}
\usepackage[a4paper,margin=1.5cm]{{geometry}}
\usepackage{{array}}
\usepackage{{longtable}}
\usepackage{{booktabs}}
\usepackage{{pdflscape}}
\usepackage{{textcomp}}
\usepackage{{lmodern}}
\usepackage{{makecell}}

\begin{{document}}

\begin{{landscape}}

\section*{{{latex_escape(title)}}}
\noindent
Range: {latex_escape(start_date_display)} --- {latex_escape(end_date_display)}

\bigskip

\footnotesize
\setlength{{\LTleft}}{{0pt}}
\setlength{{\LTright}}{{0pt}}

\begin{{longtable}}{{{column_spec}}}
\toprule
{header}
\midrule
\endfirsthead

\toprule
{header}
\midrule
\endhead

\bottomrule
\endfoot

{body}
\end{{longtable}}

\end{{landscape}}

\end{{document}}
""".strip(
        "\n"
    )

    return latex
