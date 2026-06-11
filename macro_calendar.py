"""Macro calendar — load CPI/FOMC dates and find ones near today.

The price/signal pipeline is blind to macro events; this surfaces upcoming (or
just-passed) CPI prints and FOMC decisions so the narrative can treat signals
around them with appropriate skepticism. Dates are hand-maintained in
macro_calendar.yaml. See that file for the maintenance sources.
"""

import os
from datetime import date

import yaml

MACRO_PATH = "macro_calendar.yaml"


def load_events(path=MACRO_PATH):
    """Return [{'date': date, 'event': str}], sorted by date. [] if absent/bad."""
    if not os.path.exists(path):
        return []
    try:
        raw = yaml.safe_load(open(path)) or {}
    except Exception:
        return []
    out = []
    for e in (raw.get("events") or []):
        d = e.get("date")
        if d is None:
            continue
        if not isinstance(d, date):       # yaml usually parses YYYY-MM-DD to date
            try:
                d = date.fromisoformat(str(d))
            except ValueError:
                continue
        out.append({"date": d, "event": str(e.get("event") or "")})
    return sorted(out, key=lambda x: x["date"])


def nearby_events(ahead_days=10, back_days=2, ref=None):
    """Events from `back_days` ago through `ahead_days` ahead, each annotated with
    `days` (negative = days ago, 0 = today, positive = days ahead)."""
    ref = ref or date.today()
    out = []
    for e in load_events():
        d = (e["date"] - ref).days
        if -back_days <= d <= ahead_days:
            out.append({**e, "days": d})
    return out


def when_str(days):
    """Human label for a day offset: 'today' / 'in 3d' / '2d ago'."""
    if days == 0:
        return "today"
    return f"in {days}d" if days > 0 else f"{-days}d ago"
