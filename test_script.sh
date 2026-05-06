#!/usr/bin/env bash

set -e

DB_PATH="data/test_cash_recon.db"
TEST_DIR="examples/test_week"
REPORT_DIR="reports/test_week"

echo "Cleaning old test data..."
rm -f "$DB_PATH"
rm -rf "$TEST_DIR" "$REPORT_DIR"

mkdir -p "$TEST_DIR" "$REPORT_DIR"

echo "Creating test expense files..."

cat > "$TEST_DIR/mon.txt" <<EOF
50//Milk
EOF

cat > "$TEST_DIR/tue.txt" <<EOF
30//Bread
EOF

cat > "$TEST_DIR/wed.txt" <<EOF
20//Cleaning supplies
EOF

cat > "$TEST_DIR/thu.txt" <<EOF
60//Coffee beans
15//Emergency supplies
EOF

cat > "$TEST_DIR/fri.txt" <<EOF
40//Milk
10//Packaging
EOF

cat > "$TEST_DIR/sat.txt" <<EOF
25//Bread
EOF

cat > "$TEST_DIR/sun.txt" <<EOF
35//Cleaning
EOF

echo
echo "Initializing test database..."
python src/cash_recon.py --db-path "$DB_PATH" init-db

echo
echo "Adding full week of data..."

# Monday: previous till = 0
# cash added = 300
# expenses = 50
# report = 350
python src/cash_recon.py --db-path "$DB_PATH" add-day \
  --date 2026-04-06 \
  --cash-report 350 \
  --cash-till 300 \
  --expenses-file "$TEST_DIR/mon.txt"

# Tuesday: previous till = 300
# cash added = 170
# expenses = 30
# report = 200
python src/cash_recon.py --db-path "$DB_PATH" add-day \
  --date 2026-04-07 \
  --cash-report 200 \
  --cash-till 470 \
  --expenses-file "$TEST_DIR/tue.txt"

# Wednesday: previous till = 470
# cash added = 150
# expenses = 20
# report = 170
python src/cash_recon.py --db-path "$DB_PATH" add-day \
  --date 2026-04-08 \
  --cash-report 170 \
  --cash-till 620 \
  --expenses-file "$TEST_DIR/wed.txt"

# Thursday: previous till = 620
# cash added = 280
# expenses = 75
# report = 355
python src/cash_recon.py --db-path "$DB_PATH" add-day \
  --date 2026-04-09 \
  --cash-report 355 \
  --cash-till 900 \
  --expenses-file "$TEST_DIR/thu.txt"

# Friday: previous till = 900
# cash added = 220
# expenses = 50
# report = 270
python src/cash_recon.py --db-path "$DB_PATH" add-day \
  --date 2026-04-10 \
  --cash-report 270 \
  --cash-till 1120 \
  --expenses-file "$TEST_DIR/fri.txt"

# Saturday: previous till = 1120
# cash added = 330
# expenses = 25
# report = 355
python src/cash_recon.py --db-path "$DB_PATH" add-day \
  --date 2026-04-11 \
  --cash-report 355 \
  --cash-till 1450 \
  --expenses-file "$TEST_DIR/sat.txt"

# Sunday: previous till = 1450
# cash added = 250
# expenses = 35
# report = 285
python src/cash_recon.py --db-path "$DB_PATH" add-day \
  --date 2026-04-12 \
  --cash-report 285 \
  --cash-till 1700 \
  --expenses-file "$TEST_DIR/sun.txt"

echo
echo "=============================="
echo "SHOW DAY"
echo "=============================="
python src/cash_recon.py --db-path "$DB_PATH" show-day \
  --date 2026-04-09 \
  --include-expenses

echo
echo "=============================="
echo "SHOW RANGE"
echo "=============================="
python src/cash_recon.py --db-path "$DB_PATH" show-range \
  --from 2026-04-06 \
  --to 2026-04-12 \
  --include-expenses

echo
echo "=============================="
echo "SHOW WEEK"
echo "=============================="
python src/cash_recon.py --db-path "$DB_PATH" show-week \
  --date 2026-04-09 \
  --include-expenses

echo
echo "=============================="
echo "SHOW WEEK TO DATE"
echo "=============================="
python src/cash_recon.py --db-path "$DB_PATH" show-week-to-date \
  --date 2026-04-10 \
  --include-expenses

echo
echo "=============================="
echo "EXPORT LATEX"
echo "=============================="
python src/cash_recon.py --db-path "$DB_PATH" export-range-latex \
  --from 2026-04-06 \
  --to 2026-04-12 \
  --output "$REPORT_DIR/range.tex" \
  --include-expenses

python src/cash_recon.py --db-path "$DB_PATH" export-week-latex \
  --date 2026-04-09 \
  --output "$REPORT_DIR/week.tex" \
  --include-expenses

python src/cash_recon.py --db-path "$DB_PATH" export-week-to-date-latex \
  --date 2026-04-10 \
  --output "$REPORT_DIR/week_to_date.tex" \
  --include-expenses

echo
echo "=============================="
echo "EXPORT CSV"
echo "=============================="
python src/cash_recon.py --db-path "$DB_PATH" export-range-csv \
  --from 2026-04-06 \
  --to 2026-04-12 \
  --output "$REPORT_DIR/range.csv" \
  --include-expenses

python src/cash_recon.py --db-path "$DB_PATH" export-week-csv \
  --date 2026-04-09 \
  --output "$REPORT_DIR/week.csv" \
  --include-expenses

python src/cash_recon.py --db-path "$DB_PATH" export-week-to-date-csv \
  --date 2026-04-10 \
  --output "$REPORT_DIR/week_to_date.csv" \
  --include-expenses

echo
echo "=============================="
echo "EXPORT HTML"
echo "=============================="
python src/cash_recon.py --db-path "$DB_PATH" export-range-html \
  --from 2026-04-06 \
  --to 2026-04-12 \
  --output "$REPORT_DIR/range.html"

python src/cash_recon.py --db-path "$DB_PATH" export-week-html \
  --date 2026-04-09 \
  --output "$REPORT_DIR/week.html"

python src/cash_recon.py --db-path "$DB_PATH" export-week-to-date-html \
  --date 2026-04-10 \
  --output "$REPORT_DIR/week_to_date.html"

echo
echo "Done."
echo "Test DB: $DB_PATH"
echo "Reports written to: $REPORT_DIR"
