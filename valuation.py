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
        out["pe"] = round(p / eps, 1)

    growth = _num(get("ttm_eps_growth"))
    if out["pe"] is not None and growth and growth > 0:
        out["peg"] = round(out["pe"] / growth, 2)

    ocf = _num(get("ttm_ocf"))
    shares = _num(get("shares"))
    if ocf and ocf > 0 and shares and shares > 0:
        out["p_ocf"] = round(p * shares / ocf, 1)

    return out


def valuation_tag(price, row):
    """Compact ' | PE 38.2, PEG 1.4, P/OCF 30.1' suffix for the narrative, or ''."""
    v = compute_valuation(price, row)
    parts = []
    if v["pe"]    is not None: parts.append(f"PE {v['pe']}")
    if v["peg"]   is not None: parts.append(f"PEG {v['peg']}")
    if v["p_ocf"] is not None: parts.append(f"P/OCF {v['p_ocf']}")
    return " | " + ", ".join(parts) if parts else ""
