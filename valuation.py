"""Valuation ratios (PE / PEG / P-OCF) from current price + stored TTM inputs.

These are NARRATIVE CONTEXT, not part of the conviction score (Session 34
decision). fetch_fundamentals.py stores the per-company TTM inputs (ttm_eps,
ttm_ocf, shares, ttm_eps_growth) — which change only quarterly — and the ratios
are computed here against the current price so they refresh daily without
re-fetching financials.

P-OCF (price / operating cash flow) stands in for P/FCF: Polygon's standardized
financials don't break out capex, so true free cash flow isn't reliably
available. Operating cash flow is the honest, available proxy.
"""

import pandas as pd


def _num(v):
    """Coerce to float, or None for missing/NaN/garbage."""
    try:
        if v is None or pd.isna(v):
            return None
        return float(v)
    except (TypeError, ValueError):
        return None


def compute_valuation(price, row):
    """Return {'pe', 'peg', 'p_ocf'} for one name.

    price: latest close.
    row:   dict or pandas Series with ttm_eps, ttm_ocf, shares, ttm_eps_growth.
    Any ratio that can't be computed (missing data, non-positive denominator) is
    None — valuation is optional context, never a hard requirement.
    """
    out = {"pe": None, "peg": None, "p_ocf": None}
    p = _num(price)
    if not p or p <= 0:
        return out

    get = row.get  # works for both dict and pandas Series

    eps = _num(get("ttm_eps"))
    if eps and eps > 0:
        pe = round(p / eps, 1)
        # Guard against bad underlying data (e.g. a wrong price): a sub-2 or
        # absurdly high PE here is almost always garbage, not a real bargain.
        if 2 <= pe <= 5000:
            out["pe"] = pe

    growth = _num(get("ttm_eps_growth"))
    if out["pe"] is not None and growth and growth > 0:
        out["peg"] = round(out["pe"] / growth, 2)

    ocf = _num(get("ttm_ocf"))
    shares = _num(get("shares"))
    if ocf and ocf > 0 and shares and shares > 0:
        p_ocf = round(p * shares / ocf, 1)
        # A real P/OCF below ~1 is essentially impossible (market cap < annual
        # operating cash flow); sub-1 values come from bad share counts or a bad
        # price. Keep only plausible ones.
        if 1.0 <= p_ocf <= 5000:
            out["p_ocf"] = p_ocf

    return out


def compute_forward(price, row):
    """Forward PE/PEG band from our OWN run-rate projection (no analyst feed).

    fetch_fundamentals stores three EPS-growth scenarios (bear/base/bull = min/median/
    max of the last four YoY readings). Forward EPS = TTM EPS × (1 + growth); forward
    PE = price ÷ forward EPS. base = the median-growth case; the low/high PEs bracket
    the bull/bear cases. None for pre-profit names (TTM EPS ≤ 0).
    """
    out = {"fwd_pe_base": None, "fwd_pe_low": None, "fwd_pe_high": None,
           "fwd_peg": None, "base_growth": None}
    p, eps = _num(price), _num(row.get("ttm_eps"))
    if not p or p <= 0 or not eps or eps <= 0:
        return out

    def pe_at(g):
        g = _num(g)
        if g is None:
            return None
        fwd_eps = eps * (1 + g / 100.0)
        if fwd_eps <= 0:                      # growth wipes out earnings → meaningless
            return None
        v = round(p / fwd_eps, 1)
        return v if 2 <= v <= 5000 else None

    gb = _num(row.get("eps_growth_base"))
    out["fwd_pe_base"] = pe_at(gb)
    out["fwd_pe_low"]  = pe_at(row.get("eps_growth_bull"))   # bull growth → lowest PE
    out["fwd_pe_high"] = pe_at(row.get("eps_growth_bear"))   # bear growth → highest PE
    out["base_growth"] = gb
    if out["fwd_pe_base"] is not None and gb and gb > 0:
        out["fwd_peg"] = round(out["fwd_pe_base"] / gb, 2)
    return out


def valuation_tag(price, row):
    """Compact ' | PE 38.2, PEG 1.4, P/OCF 30.1, fwd PE 25 (20-32)' suffix, or ''."""
    v = compute_valuation(price, row)
    parts = []
    if v["pe"]    is not None: parts.append(f"PE {v['pe']}")
    if v["peg"]   is not None: parts.append(f"PEG {v['peg']}")
    if v["p_ocf"] is not None: parts.append(f"P/OCF {v['p_ocf']}")
    fw = compute_forward(price, row)
    if fw["fwd_pe_base"] is not None:
        rng = ""
        if fw["fwd_pe_low"] is not None and fw["fwd_pe_high"] is not None:
            lo, hi = sorted([fw["fwd_pe_low"], fw["fwd_pe_high"]])
            rng = f" ({lo}-{hi})"
        parts.append(f"fwd PE {fw['fwd_pe_base']}{rng}")
    return " | " + ", ".join(parts) if parts else ""
