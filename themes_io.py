"""Read/write helpers for themes.yaml — the hand-curated secular-trend map.

themes.yaml is Spencer's thesis layer (thesis text, conviction, constraints, the
curated `names` and `best_in_class` per theme). The dashboard Manage tab lets you
pick which theme(s) a newly-added name belongs to, so the universe add is fully
turn-key (no hand-editing the YAML on the server).

These writers are deliberately LINE-BASED, not a yaml.safe_load → safe_dump
round-trip: a full re-dump would strip the file's comments and the carefully
written thesis/constraint prose. We only ever touch the one-line `names: [...]`
(and, on remove, `best_in_class: [...]`) list under each theme, leaving every
other line — comments included — byte-identical.
"""

import os
import re

import yaml

THEMES_PATH = "themes.yaml"

# A bare top-level theme key, e.g. `AI_Infrastructure:` (value is on the indented
# lines below it, so the key line itself ends right after the colon).
_THEME_KEY = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*):\s*$")
# An inline list field, e.g. `  names: [NVDA, AVGO]` or `  best_in_class: [NVDA]`.
_LIST_LINE = re.compile(r"^(\s*(names|best_in_class):\s*)\[(.*)\]\s*$")


def load_themes(path=THEMES_PATH):
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}


def theme_options(path=THEMES_PATH):
    """[(id, display_name, conviction), ...] for the dashboard selector.

    Excludes the Bond_Market regime theme — it's monitor-only (TLT), never a
    bucket you'd assign a company to.
    """
    themes = load_themes(path)
    return [
        (tid, meta.get("name", tid), meta.get("conviction", "medium"))
        for tid, meta in themes.items()
        if tid != "Bond_Market"
    ]


def _split_items(inner):
    return [x.strip() for x in inner.split(",") if x.strip()]


def add_ticker_to_themes(ticker, theme_ids, path=THEMES_PATH):
    """Append `ticker` to the `names` list of each theme in `theme_ids`.

    Only touches `names` (not `best_in_class` — that's Spencer's 1-2 favorites,
    a manual call). Idempotent: a ticker already present is left as-is. Returns
    the list of theme ids actually changed.
    """
    ticker = ticker.upper()
    want = set(theme_ids)
    if not want:
        return []

    with open(path) as f:
        lines = f.readlines()

    current = None
    changed = []
    for i, line in enumerate(lines):
        m = _THEME_KEY.match(line)
        if m:
            current = m.group(1)
            continue
        if current not in want:
            continue
        lm = _LIST_LINE.match(line)
        if lm and lm.group(2) == "names":
            prefix, inner = lm.group(1), lm.group(3)
            items = _split_items(inner)
            if ticker not in items:
                items.append(ticker)
                lines[i] = f"{prefix}[{', '.join(items)}]\n"
                changed.append(current)

    if changed:
        with open(path, "w") as f:
            f.writelines(lines)
    return changed


def remove_ticker_from_themes(ticker, path=THEMES_PATH):
    """Remove `ticker` from every `names` and `best_in_class` list it appears in.

    Mirrors the universe remove so a dropped name leaves no dangling theme
    reference. Returns the list of theme ids changed.
    """
    ticker = ticker.upper()
    if not os.path.exists(path):
        return []

    with open(path) as f:
        lines = f.readlines()

    current = None
    changed = set()
    for i, line in enumerate(lines):
        m = _THEME_KEY.match(line)
        if m:
            current = m.group(1)
            continue
        lm = _LIST_LINE.match(line)
        if lm:
            prefix, inner = lm.group(1), lm.group(3)
            items = _split_items(inner)
            if ticker in items:
                items = [x for x in items if x != ticker]
                lines[i] = f"{prefix}[{', '.join(items)}]\n"
                changed.add(current)

    if changed:
        with open(path, "w") as f:
            f.writelines(lines)
    return sorted(changed)
