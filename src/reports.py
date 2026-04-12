from __future__ import annotations

from decimal import Decimal
from typing import Any
import csv
from pathlib import Path


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
        column_spec = r"p{3.2cm} r r r r r | r r r r r"
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
def write_range_csv(
        output_path: str | Path,
        range_rows: list[dict[str, Any]],
        include_expenses: bool = False,
        ) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
            "date",
            "has_data",
            "cash_in_report",
            "cash_in_till",
            "expenses_total",
            "till_plus_expenses",
            "difference",
            "cum_cash_in_report",
            "cum_cash_in_till",
            "cum_expenses_total",
            "cum_till_plus_expenses",
            "cum_difference",
            ]

    if include_expenses:
        fieldnames.append("expense_details")

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for row in range_rows:
            output_row = {
                    "date": row["date"],
                    "has_data": "yes" if row["has_data"] else "no",
                    "cash_in_report": format_money(row["cash_in_report"]) if row["has_data"] else "",
                    "cash_in_till": format_money(row["cash_in_till"]) if row["has_data"] else "",
                    "expenses_total": format_money(row["expenses_total"]) if row["has_data"] else "",
                    "till_plus_expenses": format_money(row["till_plus_expenses"]) if row["has_data"] else "",
                    "difference": format_money(row["difference"]) if row["has_data"] else "",
                    "cum_cash_in_report": format_money(row["cum_cash_in_report"]),
                    "cum_cash_in_till": format_money(row["cum_cash_in_till"]),
                    "cum_expenses_total": format_money(row["cum_expenses_total"]),
                    "cum_till_plus_expenses": format_money(row["cum_till_plus_expenses"]),
                    "cum_difference": format_money(row["cum_difference"]),
                    }

            if include_expenses:
                expense_lines: list[str] = []
                for expense in row["expenses"]:
                    amount = format_money(Decimal(str(expense["amount"])))
                    description = str(expense["description"]).strip()
                    if description:
                        expense_lines.append(f"{amount} -- {description}")
                    else:
                        expense_lines.append(amount)

                output_row["expense_details"] = "\n".join(expense_lines)

            writer.writerow(output_row)

def html_escape(text: str) -> str:
    replacements = {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
    }
    return "".join(replacements.get(char, char) for char in text)


def generate_range_html(
    title: str,
    start_date_display: str,
    end_date_display: str,
    range_rows: list[dict[str, Any]],
) -> str:
    body_rows: list[str] = []

    for index, row in enumerate(range_rows):
        row_id = f"expenses-{index}"
        display_date = html_escape(row["date"])

        if row["has_data"]:
            if row["expenses"]:
                expenses_cell = (
                    f'<button type="button" class="expenses-button" '
                    f'onclick="toggleExpenses(\'{row_id}\')">'
                    f'{format_money(row["expenses_total"])} ▾'
                    f'</button>'
                )
            else:
                expenses_cell = format_money(row["expenses_total"])

            main_row = f"""
<tr class="{'empty-day' if not row['has_data'] else ''}">
  <td>{display_date}</td>
  <td>{format_money(row["cash_in_report"])}</td>
  <td>{format_money(row["cash_in_till"])}</td>
  <td>{expenses_cell}</td>
  <td>{format_money(row["till_plus_expenses"])}</td>
  <td>{format_money(row["difference"])}</td>
  <td class="separator-left">{format_money(row["cum_cash_in_report"])}</td>
  <td>{format_money(row["cum_cash_in_till"])}</td>
  <td>{format_money(row["cum_expenses_total"])}</td>
  <td>{format_money(row["cum_till_plus_expenses"])}</td>
  <td>{format_money(row["cum_difference"])}</td>
</tr>
""".strip()

            body_rows.append(main_row)

            if row["expenses"]:
                expense_items: list[str] = []
                for expense in row["expenses"]:
                    amount = format_money(Decimal(str(expense["amount"])))
                    description = str(expense["description"]).strip()
                    if description:
                        item = (
                            f"<li>£{amount} — {html_escape(description)}</li>"
                        )
                    else:
                        item = f"<li>£{amount}</li>"
                    expense_items.append(item)

                expenses_row = f"""
<tr id="{row_id}" class="expenses-row">
  <td colspan="11" class="expenses-cell">
    <strong>Expenses for {display_date}:</strong>
    <ul class="expenses-list">
      {"".join(expense_items)}
    </ul>
  </td>
</tr>
""".strip()

                body_rows.append(expenses_row)

        else:
            main_row = f"""
<tr class="empty-day">
  <td>{display_date}</td>
  <td>-</td>
  <td>-</td>
  <td>-</td>
  <td>-</td>
  <td>-</td>
  <td class="separator-left">{format_money(row["cum_cash_in_report"])}</td>
  <td>{format_money(row["cum_cash_in_till"])}</td>
  <td>{format_money(row["cum_expenses_total"])}</td>
  <td>{format_money(row["cum_till_plus_expenses"])}</td>
  <td>{format_money(row["cum_difference"])}</td>
</tr>
""".strip()

            body_rows.append(main_row)

    table_rows = "\n".join(body_rows)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{html_escape(title)}</title>
  <style>
    body {{
      font-family: Arial, sans-serif;
      margin: 24px;
      color: #222;
    }}

    h1 {{
      margin-top: 0;
      margin-bottom: 8px;
    }}

    p {{
      margin-top: 0;
      margin-bottom: 16px;
    }}

    table {{
      border-collapse: collapse;
      width: 100%;
      font-size: 14px;
    }}

    th, td {{
      border: 1px solid #999;
      padding: 8px 10px;
      text-align: right;
      vertical-align: top;
    }}

    th:first-child,
    td:first-child {{
      text-align: left;
      white-space: nowrap;
    }}

    .separator-left {{
      border-left: 3px solid #444 !important;
    }}

    .expenses-button {{
      padding: 4px 8px;
      cursor: pointer;
    }}

    .expenses-row {{
      display: none;
    }}

    .expenses-row.open {{
      display: table-row;
    }}

    .expenses-cell {{
      text-align: left;
      background: #f7f7f7;
    }}

    .expenses-list {{
      margin: 8px 0 0 0;
      padding-left: 20px;
    }}

    .expenses-list li {{
      margin: 4px 0;
    }}

    .empty-day {{
      color: #666;
    }}
  </style>
</head>
<body>
  <h1>{html_escape(title)}</h1>
  <p><strong>Range:</strong> {html_escape(start_date_display)} — {html_escape(end_date_display)}</p>

  <table>
    <thead>
      <tr>
        <th>Date</th>
        <th>Cash Rep</th>
        <th>Cash Till</th>
        <th>Expenses</th>
        <th>Till+Exp</th>
        <th>Diff</th>
        <th class="separator-left">Cum Rep</th>
        <th>Cum Till</th>
        <th>Cum Exp</th>
        <th>Cum T+E</th>
        <th>Cum Diff</th>
      </tr>
    </thead>
    <tbody>
      {table_rows}
    </tbody>
  </table>

  <script>
    function toggleExpenses(rowId) {{
      const row = document.getElementById(rowId);
      if (!row) {{
        return;
      }}
      row.classList.toggle("open");
    }}
  </script>
</body>
</html>
"""
    return html


def write_html_file(path: str | Path, content: str) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
