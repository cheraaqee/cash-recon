python - <<'PY'
from pathlib import Path

p = Path("src/reports.py")
text = p.read_text()

text = text.replace("cum_cash_in_till", "cum_cash_added_to_till")
text = text.replace("cum_till_plus_expenses", "cum_reconciled_total")
text = text.replace("till_plus_expenses", "reconciled_total")

p.write_text(text)
PY
