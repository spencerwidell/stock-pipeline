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

import yaml

HOLDINGS_PATH = "holdings.yaml"
_META_KEYS = {"portfolio", "positions", "overrides"}


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
