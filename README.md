# cash-recon

A CLI-based cash reconciliation tool for small businesses (e.g. cafés) that tracks daily cash, expenses, and generates reports in multiple formats (CLI, LaTeX, CSV, HTML).

---

## 📌 Purpose

This tool helps reconcile:

- **Cash sales (from POS/report)**
- **Cash physically in the till**
- **Cash expenses taken from the till**

### Core relationship

```
cash_in_till + expenses = cash_in_report
```

Any mismatch is immediately visible.

---

## ✨ Features

- 📅 Daily cash report entry
- 🧾 Expense tracking with optional descriptions
- 📊 Reports:
  - Day
  - Range
  - Week (Mon–Sun)
  - Week-to-date
- 🔢 Automatic cumulative totals
- 📄 Export formats:
  - CLI (terminal)
  - LaTeX (PDF-ready)
  - CSV (spreadsheet-friendly)
  - HTML (browser view with expandable expenses)
- ⚡ Minimal data entry (expense file input)
- 🧠 Clean and auditable structure

---

## 🏗️ Project Structure

```
cash-recon/
├── src/
│   ├── cash_recon.py   # CLI entry point
│   ├── db.py           # SQLite database logic
│   ├── parser.py       # Expense file parser
│   ├── reports.py      # Report generation (CLI, LaTeX, CSV, HTML)
│   ├── services.py     # Data aggregation logic
│   └── utils.py        # Date and formatting helpers
├── data/
│   └── cash_recon.db   # SQLite database (created at runtime)
├── reports/            # Generated outputs
├── examples/           # Sample expense files
└── README.md
```

---

## ⚙️ Setup

### 1. Clone the repo

```bash
git clone <repo-url>
cd cash-recon
```

### 2. Create virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 🚀 Usage

### Initialize database

```bash
python src/cash_recon.py init-db
```

---

## 🧾 Expense File Format

Each line represents one expense:

```
amount//description
```

Examples:

```
18.50//Milk
7.20//Cleaning spray
12
4.75//Bread
```

Rules:

- `//description` is optional
- one expense per line
- blank lines ignored

---

## ➕ Add Daily Report

```bash
python src/cash_recon.py add-day \
  --date 2026-04-07 \
  --cash-report 500 \
  --cash-till 380 \
  --expenses-file examples/day.txt
```

If `--date` is omitted, today's date is used.

---

## 📊 View Reports

### Day

```bash
python src/cash_recon.py show-day --date 2026-04-07
```

With expenses:

```bash
python src/cash_recon.py show-day --date 2026-04-07 --include-expenses
```

---

### Range

```bash
python src/cash_recon.py show-range \
  --from 2026-04-01 \
  --to 2026-04-10
```

---

### Week

```bash
python src/cash_recon.py show-week --date 2026-04-07
```

---

### Week-to-date

```bash
python src/cash_recon.py show-week-to-date
```

---

## 📄 Export Reports

### LaTeX

```bash
python src/cash_recon.py export-week-latex \
  --date 2026-04-07 \
  --output reports/week.tex
```

---

### CSV

```bash
python src/cash_recon.py export-range-csv \
  --from 2026-04-01 \
  --to 2026-04-10 \
  --output reports/report.csv
```

---

### HTML (with expandable expenses)

```bash
python src/cash_recon.py export-week-html \
  --date 2026-04-07 \
  --output reports/week.html
```

Open in browser:

```bash
xdg-open reports/week.html
```

---

## 🌐 HTML Report Features

- Clean tabular layout
- Weekly / range views
- Cumulative totals
- Expandable expense rows per day
- No server required (static file)

---

## 🧠 Design Principles

- **Single source of truth**: SQLite database
- **Separation of concerns**:
  - data (db.py)
  - parsing (parser.py)
  - logic (services.py)
  - output (reports.py)
- **Compute, don’t store**:
  - totals calculated at runtime
- **Minimal user friction**:
  - text-based expense input
- **Auditability**:
  - every expense stored individually

---

## ⚠️ Notes

- Dates are stored as `YYYY-MM-DD`
- Weeks run **Monday → Sunday**
- Missing days are shown in reports
- No restriction on mismatches (difference ≠ 0)

---

## 💾 Backup Recommendation

Back up your database periodically:

```bash
cp data/cash_recon.db backups/cash_recon_$(date +%F).db
```

---

## 🔮 Future Improvements

- Highlight mismatched days
- Edit/delete commands
- Summary analytics
- Optional web UI
- Multi-user support

---

## 📜 License

MIT (or your preferred license)

---

## 👤 Author

Built for practical daily use in a café environment.
