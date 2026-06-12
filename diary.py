"""Investor diary — a simple, append-only log of the actions you actually took.

Fixed schema, the same fields every time:
    date, ticker, action, trade_pct, new_weight, recommendation, note

Each row records BOTH halves of a trade so allocations stay reconstructable:
  - trade_pct   the signed amount you transacted (AVGO +8, SOFI -5, RTX +3)
  - new_weight  the RESULTING position size (AVGO 15, SOFI 3, RTX 3)

new_weight is the canonical number the dashboard writes back into holdings.yaml
(via holdings_io.apply_trade), so logging a trade keeps the weight snapshot current
automatically. holdings.yaml stays the current-weight SNAPSHOT; this diary is the
ACTION HISTORY ("on 2026-06-13 I added GOOG to 6% on the core-weakness call").

AWS-authoritative and gitignored (it's personal data, written from the dashboard on
the live server). Back it up with the dashboard's Download button.
"""

import csv
import os
from datetime import date

DIARY_PATH = "investor_diary.csv"
FIELDS  = ["date", "ticker", "action", "trade_pct", "new_weight", "recommendation", "note"]
ACTIONS = ["BUY", "ADD", "TRIM", "SELL", "PASS"]   # PASS = considered, chose not to act

# The pre-Session-45 schema had a single ambiguous `weight` column. Files written
# under it are migrated forward on first write (see _ensure_schema).
_LEGACY_FIELDS = ["date", "ticker", "action", "weight", "recommendation", "note"]


def _clean(x):
    return " ".join(str(x or "").split())


def _read_header(path):
    try:
        with open(path, newline="") as f:
            return next(csv.reader(f), None)
    except Exception:
        return None


def _ensure_schema(path):
    """If `path` is on the legacy schema, rewrite it under FIELDS in place.

    Best-effort split of the old `weight`: an ADD recorded a delta (the Log button
    logged the suggested add amount) → trade_pct; everything else recorded a target
    size → new_weight. Eyeball any ADD rows after migration — they keep the delta,
    not the resulting size.
    """
    if not os.path.exists(path) or _read_header(path) != _LEGACY_FIELDS:
        return
    with open(path, newline="") as f:
        old = list(csv.DictReader(f))
    rows = []
    for r in old:
        w = _clean(r.get("weight"))
        is_delta = (r.get("action") or "").upper() == "ADD"
        rows.append({
            "date":           r.get("date", ""),
            "ticker":         r.get("ticker", ""),
            "action":         r.get("action", ""),
            "trade_pct":      w if is_delta else "",
            "new_weight":     "" if is_delta else w,
            "recommendation": r.get("recommendation", ""),
            "note":           r.get("note", ""),
        })
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)


def log_action(ticker, action, trade_pct="", new_weight="", recommendation="", note="",
               on=None, path=DIARY_PATH):
    """Append one action to the diary. Returns the row written."""
    _ensure_schema(path)
    row = {
        "date":           on or date.today().isoformat(),
        "ticker":         str(ticker or "").upper().strip(),
        "action":         str(action or "").upper().strip(),
        "trade_pct":      _clean(trade_pct),
        "new_weight":     _clean(new_weight),
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
    """Return the diary as a DataFrame (empty with the right columns if none yet).

    Tolerates a legacy file: it's reindexed onto FIELDS so old rows still render
    (a one-time migration to the real columns happens on the next log_action).
    """
    import pandas as pd
    if not os.path.exists(path):
        return pd.DataFrame(columns=FIELDS)
    try:
        df = pd.read_csv(path, dtype=str).fillna("")
    except Exception:
        return pd.DataFrame(columns=FIELDS)
    if "weight" in df.columns and "new_weight" not in df.columns:
        df = df.rename(columns={"weight": "new_weight"})
    return df.reindex(columns=FIELDS).fillna("")


if __name__ == "__main__":
    log_action("GOOG", "BUY", trade_pct="+3", new_weight="3",
               recommendation="NEW SETUP", note="first diary line")
    print(load_diary().to_string(index=False))
