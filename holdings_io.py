"""Single source of truth for reading holdings.yaml.

Spencer maintains exactly ONE file. Everything else in the portfolio-intelligence
system (tier classification, theme mapping, stop tracking, cash deployment) is
derived from it — never hand-maintained.

Schema (Session 36):

    portfolio:
      total_value: 1300000          # approximate $ — turns weights into dollars
      bi_weekly_contribution: 1600  # used to size deployment suggestions
    positions:
      NVDA: 11                      # one line per holding, just the % weight
      ...
      CASH: 16                      # money-market dry powder
    overrides:
      TSLA: core                    # only when auto-classification would be wrong

Back-compatible with the OLD flat schema (TICKER: weight at the top level), so a
stale deploy can't crash the loaders mid-rollout.
"""

import os
import re

import yaml

HOLDINGS_PATH = "holdings.yaml"
_META_KEYS = {"portfolio", "positions", "overrides"}

# A line inside the positions: block, e.g. `  NVDA: 11` or `  ELF:  10` (the
# alignment spaces are preserved by capturing everything up to the value).
_POS_LINE = re.compile(r"^(\s+)([A-Za-z][A-Za-z0-9._-]*)(:\s*)(.*?)\s*$")


def _raw(path=HOLDINGS_PATH):
    if not os.path.exists(path):
        return {}
    try:
        with open(path) as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def _positions_block(raw):
    """The ticker→weight mapping — from `positions:` (new) or the top level (old flat)."""
    if isinstance(raw.get("positions"), dict):
        return raw["positions"]
    return {k: v for k, v in raw.items() if k not in _META_KEYS}


def _num(x, default=0.0):
    try:
        return float(str(x).replace("$", "").replace("%", "").replace(",", "").strip())
    except (TypeError, ValueError):
        return default


def load_positions(path=HOLDINGS_PATH, include_cash=False):
    """{TICKER: 'weight'} (weights kept as strings for display).

    CASH is excluded by default; pass include_cash=True for readers that surface
    CASH alongside the stock holdings.
    """
    pos = _positions_block(_raw(path))
    out = {}
    for k, v in pos.items():
        tk = str(k).upper()
        if v is None or (tk == "CASH" and not include_cash):
            continue
        out[tk] = str(v).strip()
    return out


def load_cash(path=HOLDINGS_PATH):
    """CASH weight (%) as a float; 0.0 if absent."""
    for k, v in _positions_block(_raw(path)).items():
        if str(k).upper() == "CASH":
            return _num(v, 0.0)
    return 0.0


def load_portfolio_meta(path=HOLDINGS_PATH):
    """{'total_value', 'bi_weekly_contribution'} — 0.0 each if absent."""
    p = _raw(path).get("portfolio") or {}
    return {"total_value": _num(p.get("total_value"), 0.0),
            "bi_weekly_contribution": _num(p.get("bi_weekly_contribution"), 0.0)}


def load_overrides(path=HOLDINGS_PATH):
    """{TICKER: 'core'|'speculative'} from the overrides: block (lower-cased)."""
    ov = _raw(path).get("overrides") or {}
    return {str(k).upper(): str(v).strip().lower() for k, v in ov.items() if v}


# ---------------------------------------------------------------------------
# Writer — apply a logged trade back to holdings.yaml (Session 45)
# ---------------------------------------------------------------------------
# The diary now logs the RESULTING position size (new_weight); applying it here
# keeps the snapshot from going stale after every trade. Like themes_io, this is
# a LINE-BASED edit (never a yaml re-dump) so the file's comments and the
# carefully-written schema prose stay byte-identical — only the one weight line
# (and the offsetting CASH line) change.

def _fmt_weight(w):
    """Match the file's bare-number style: 15 not 15.0, but 4.2 stays 4.2."""
    w = round(float(w), 1)
    return str(int(w)) if w == int(w) else f"{w:g}"


def _positions_bounds(lines):
    """(start, end) line indices spanning the positions: block body, or None.

    start = first body line after `positions:`; end = one past the last body
    line (the next top-level key or EOF). Body lines are the indented entries.
    """
    start = None
    for i, line in enumerate(lines):
        if re.match(r"^positions:\s*$", line):
            start = i + 1
            break
    if start is None:
        return None
    end = len(lines)
    for j in range(start, len(lines)):
        s = lines[j]
        if s.strip() and not s[0].isspace():   # a new top-level key ends the block
            end = j
            break
    return start, end


def apply_trade(ticker, new_weight, path=HOLDINGS_PATH):
    """Set `ticker` to `new_weight` (%) in positions: and offset CASH by the delta.

    A trade just moves weight between the position and cash, so the book still
    sums to 100. Inserts a line for a brand-new holding; removes it on a full exit
    (new_weight <= 0). Returns a summary dict, or None if the file/block is absent.
    """
    ticker = str(ticker or "").upper().strip()
    if not ticker or ticker == "CASH" or not os.path.exists(path):
        return None
    new_weight = round(float(new_weight), 1)

    with open(path) as f:
        lines = f.readlines()
    bounds = _positions_bounds(lines)
    if bounds is None:
        return None
    start, end = bounds

    tk_idx = cash_idx = None
    indent = "  "
    old_w = 0.0
    for i in range(start, end):
        m = _POS_LINE.match(lines[i])
        if not m:
            continue
        name = m.group(2).upper()
        indent = m.group(1)            # adopt the file's indent for any insert
        if name == ticker:
            tk_idx, old_w = i, _num(m.group(4), 0.0)
        elif name == "CASH":
            cash_idx = i

    delta = round(new_weight - old_w, 1)
    cash_old = _num(lines[cash_idx].split(":", 1)[1], 0.0) if cash_idx is not None else 0.0
    cash_new = round(cash_old - delta, 1)

    # Rewrite the ticker line (or insert / delete it).
    if new_weight <= 0:
        if tk_idx is not None:
            del lines[tk_idx]
            if cash_idx is not None and cash_idx > tk_idx:
                cash_idx -= 1
    elif tk_idx is not None:
        m = _POS_LINE.match(lines[tk_idx])
        lines[tk_idx] = f"{m.group(1)}{m.group(2)}{m.group(3)}{_fmt_weight(new_weight)}\n"
    else:
        ins = cash_idx if cash_idx is not None else end   # keep CASH last
        lines.insert(ins, f"{indent}{ticker}: {_fmt_weight(new_weight)}\n")
        if cash_idx is not None and ins <= cash_idx:
            cash_idx += 1

    # Offset CASH so the book still sums to 100.
    if cash_idx is not None:
        cm = _POS_LINE.match(lines[cash_idx])
        lines[cash_idx] = f"{cm.group(1)}{cm.group(2)}{cm.group(3)}{_fmt_weight(cash_new)}\n"

    with open(path, "w") as f:
        f.writelines(lines)
    return {"ticker": ticker, "old": old_w, "new": new_weight,
            "cash_old": cash_old, "cash_new": cash_new}
