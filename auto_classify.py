"""Auto-classifier — CORE vs SPECULATIVE, derived from evidence, never stored.

Spencer maintains only holdings.yaml. Each position is classified fresh (at dashboard
load and pipeline close) from the signal stack:

  CORE  — earn a seat by being a quality name in a real secular trend, sized as a
          conviction position. HELD THROUGH VOLATILITY: price never forces it out;
          only a broken thesis (moat/fundamental erosion, theme drop) does. No stop.
  SPEC  — everything that hasn't earned core: thin moat, weak/again deteriorating
          fundamentals, no secular theme, or a deep drawdown. Competes on evidence
          and lives under the −7% stop discipline.

Precedence (resolves every conflict):
  1. An investor override in holdings.yaml always wins.
  2. Else CORE if it meets ALL core conditions.
  3. Else SPECULATIVE, with the failing/triggering reasons spelled out.

Note on a deep drawdown: a name that is otherwise core-quality but down ≥40% from its
high stays CORE — for a wide-moat secular leader that is a BUY-WEAKNESS signal, not a
stop (see memory core-vs-speculative-framing: price level alone is not a core trigger).
The −40% rule only demotes names that don't otherwise earn core.

Reuses theme_engine for per-name signal/quality/theme data — one source of truth.
"""

import holdings_io
import theme_engine

CONV_RANK     = {"high": 2, "medium": 1, "low": 0}
DEEP_DRAWDOWN = -40.0   # dist_52w_high (%) at/below this = down ≥40% from the high
MIN_CORE_WEIGHT = 2.0   # a sub-2% sliver is a starter, not a conviction core position


def _theme_index():
    """ticker -> {'themes': [names], 'max_conv': 'high'|'medium'|'low'|None}."""
    idx = {}
    for tid, meta in theme_engine.load_themes().items():
        if tid == theme_engine.REGIME_THEME:
            continue
        conv = meta.get("conviction", "medium")
        for tk in (meta.get("names") or []):
            e = idx.setdefault(tk, {"themes": [], "max_conv": None})
            e["themes"].append(meta.get("name", tid))
            if e["max_conv"] is None or CONV_RANK.get(conv, 0) > CONV_RANK.get(e["max_conv"], -1):
                e["max_conv"] = conv
    return idx


def _weight(w):
    try:
        return float(str(w).replace("%", "").strip())
    except (TypeError, ValueError):
        return 0.0


def classify_position(ticker, weight, ns, theme_info, override=None):
    """Classify one held name. Returns a dict with tier + reasoning + evidence."""
    themes  = theme_info.get("themes", []) if theme_info else []
    max_conv = theme_info.get("max_conv") if theme_info else None
    moat = ns.get("moat_rating") if ns else None
    fund = ns.get("fundamental_score") if ns else None
    off_high = ns.get("dist_52w_high") if ns else None

    evidence = {"moat": moat, "fundamental": fund, "themes": themes,
                "max_conv": max_conv, "weight": weight, "dist_52w_high": off_high}

    if override == "core":
        return {"ticker": ticker, "tier": "CORE", "override": True,
                "reasons": ["Investor override → CORE (held through volatility, no stop)"],
                "evidence": evidence}
    if override == "speculative":
        return {"ticker": ticker, "tier": "SPECULATIVE", "override": True,
                "reasons": ["Investor override → SPECULATIVE (−7% stop discipline)"],
                "evidence": evidence}

    # --- CORE eligibility: all four must hold ---
    c_moat   = moat is not None and moat >= 4
    c_fund   = fund is None or fund >= 4          # missing F (e.g. international) doesn't block
    c_theme  = bool(themes) and max_conv in ("high", "medium")
    c_weight = weight > MIN_CORE_WEIGHT

    if c_moat and c_fund and c_theme and c_weight:
        reasons = [f"wide moat ({moat}/5)",
                   (f"strong fundamentals ({fund}/5)" if fund is not None
                    else "fundamentals n/a (international) — not blocking"),
                   f"in a {max_conv}-conviction theme ({themes[0]})",
                   f"sized as a position ({weight:.0f}%)"]
        if off_high is not None and off_high <= DEEP_DRAWDOWN:
            reasons.append(f"down {abs(off_high):.0f}% from high — buy-weakness, NOT a stop")
        return {"ticker": ticker, "tier": "CORE", "override": False,
                "reasons": reasons, "evidence": evidence}

    # --- SPECULATIVE: explain which triggers fired / core conditions failed ---
    reasons = []
    if moat is not None and moat <= 2:
        reasons.append(f"thin moat ({moat}/5)")
    elif not c_moat:
        reasons.append(f"moat {moat}/5 below core bar (≥4)" if moat is not None
                       else "moat n/a")
    if fund is not None and fund <= 2:
        reasons.append(f"weak fundamentals ({fund}/5)")
    elif fund is not None and fund < 4:
        reasons.append(f"fundamentals {fund}/5 below core bar (≥4)")
    if not themes:
        reasons.append("maps to no secular theme")
    elif max_conv not in ("high", "medium"):
        reasons.append(f"only in a {max_conv}-conviction theme")
    if off_high is not None and off_high <= DEEP_DRAWDOWN:
        reasons.append(f"down {abs(off_high):.0f}% from 52-wk high")
    if weight <= MIN_CORE_WEIGHT:
        reasons.append(f"tiny position ({weight:.0f}%) — a starter, not core")
    if not reasons:
        reasons.append("does not meet all core conditions")
    return {"ticker": ticker, "tier": "SPECULATIVE", "override": False,
            "reasons": reasons, "evidence": evidence}


def tier_for_new(ns, theme_info):
    """Tier a NOT-held candidate (gap starter / beaten-down idea). Conservative:
    CORE only when moat≥4 AND fundamental≥4 AND in a high/medium theme; else
    SPECULATIVE (a new buy with missing/soft evidence gets stop discipline)."""
    moat = ns.get("moat_rating") if ns else None
    fund = ns.get("fundamental_score") if ns else None
    max_conv = theme_info.get("max_conv") if theme_info else None
    if (moat is not None and moat >= 4 and fund is not None and fund >= 4
            and max_conv in ("high", "medium")):
        return "CORE"
    return "SPECULATIVE"


def classify_holdings():
    """Classify every current holding. Returns
    {classifications: [...], core: [tickers], speculative: [tickers]}."""
    holdings  = holdings_io.load_positions()          # {TICKER: 'weight'} excl CASH
    overrides = holdings_io.load_overrides()
    sig       = theme_engine._load_signals()
    tidx      = _theme_index()

    out = []
    for tk, w in holdings.items():
        ns = theme_engine._name_status(tk, sig, holdings)
        out.append(classify_position(tk, _weight(w), ns, tidx.get(tk),
                                      override=overrides.get(tk)))
    out.sort(key=lambda c: (c["tier"] != "CORE", c["ticker"]))
    return {
        "classifications": out,
        "core": [c["ticker"] for c in out if c["tier"] == "CORE"],
        "speculative": [c["ticker"] for c in out if c["tier"] == "SPECULATIVE"],
    }


if __name__ == "__main__":
    res = classify_holdings()
    print(f"CORE ({len(res['core'])}): {', '.join(res['core'])}")
    print(f"SPECULATIVE ({len(res['speculative'])}): {', '.join(res['speculative'])}")
    print("-" * 70)
    for c in res["classifications"]:
        ov = " [override]" if c["override"] else ""
        print(f"{c['ticker']:6} {c['tier']:12}{ov}")
        for r in c["reasons"]:
            print(f"        · {r}")
