"""Investor diary — a simple, append-only log of the actions you actually took.

Fixed schema, the same fields every time:
    date, ticker, action, weight, recommendation, note

This is the ACTION HISTORY ("on 2026-06-13 I added GOOG 6% on the core-weakness
call"). holdings.yaml stays the current-weight SNAPSHOT — not a ledger. The diary
complements it: log what you did and why, so we can look back and learn.

AWS-authoritative and gitignored (it's personal data, written from the dashboard on
the live server). Back it up with the dashboard's Download button.
"""

import csv
import os
from datetime import date

DIARY_PATH = "investor_diary.csv"
FIELDS  = ["date", "ticker", "action", "weight", "recommendation", "note"]
ACTIONS = ["BUY", "ADD", "TRIM", "SELL", "PASS"]   # PASS = considered, chose not to act


def _clean(x):
    return " ".join(str(x or "").split())


def log_action(ticker, action, weight="", recommendation="", note="", on=None,
               path=DIARY_PATH):
    """Append one action to the diary. Returns the row written."""
    row = {
        "date":           on or date.today().isoformat(),
        "ticker":         str(ticker or "").upper().strip(),
        "action":         str(action or "").upper().strip(),
        "weight":         _clean(weight),
        "recommendation": _clean(recommendation),
        "note":           _clean(note),
    }
    exists = os.path.exists(path)
    with open(path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if not exists:
            w.writeheader()
        w.writerow(row)
    return row


def load_diary(path=DIARY_PATH):
    """Return the diary as a DataFrame (empty with the right columns if none yet)."""
    import pandas as pd
    if not os.path.exists(path):
        return pd.DataFrame(columns=FIELDS)
    try:
        return pd.read_csv(path, dtype=str).fillna("")
    except Exception:
        return pd.DataFrame(columns=FIELDS)


if __name__ == "__main__":
    log_action("GOOG", "ADD", "6%", "demo entry", "first diary line")
    print(load_diary().to_string(index=False))
