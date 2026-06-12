"""Theme engine — overlays Spencer's secular-trend map (themes.yaml) on the live
signals so the dashboard and alerts can reason about portfolio coverage by theme,
gaps, concentration, best entries, and the bond-market regime.

Two public entry points:
  get_theme_status()             -> per-theme detail (names, best-in-class, held,
                                    gap, best entry now) + the TLT regime
  get_portfolio_theme_coverage() -> portfolio-level summary (coverage, gaps,
                                    concentration, held count vs target, regime)

Self-contained signal loader (does NOT import narrative_alert) so narrative_alert
can import this without a circular dependency.
"""

import os
from datetime import date

import duckdb
import pandas as pd
import yaml

import holdings_io
import valuation

THEMES_PATH   = "themes.yaml"
VSA_PATH      = "data/stock_vsa.parquet"
FUND_PATH     = "data/fundamentals.parquet"
MOAT_PATH     = "data/moat.parquet"
HOLDINGS_PATH = "holdings.yaml"

REGIME_THEME   = "Bond_Market"   # monitor-only; excluded from coverage counts
TLT_TICKER     = "TLT"

# Optional annotations for holdings that map to no theme. Absence of a note just
# means "off-thesis" with no further qualifier (e.g. ELF — genuinely discretionary).
OFF_THESIS_NOTES = {
}
TARGET_MIN     = 10              # held-positions target band
TARGET_MAX     = 15
CONCENTRATION  = 3              # >= this many held in one theme = concentrated


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------
def load_themes(path=THEMES_PATH):
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}


def load_holdings(path=HOLDINGS_PATH):
    """{TICKER: 'weight'} excluding CASH. Empty if absent/unreadable."""
    return holdings_io.load_positions(path)


def _load_signals():
    """Latest bar per ticker + fundamentals/valuation/moat, indexed by ticker."""
    df = duckdb.query("""
        WITH latest AS (
            SELECT ticker, date, close, wl_state, conviction_score, channel_zone,
                   channel_pos, flip_price, flip_date, resistance,
                   high_52w, low_52w, dist_52w_high, dist_52w_low,
                   ROUND((close - flip_price) / flip_price * 100, 1) AS gap_from_flip,
                   ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY date DESC) AS rn
            FROM 'data/stock_vsa.parquet'
        )
        SELECT * EXCLUDE (rn) FROM latest WHERE rn = 1
    """).df()

    if os.path.exists(FUND_PATH):
        fund_all = pd.read_parquet(FUND_PATH)
        keep = [c for c in ["ticker", "fundamental_score", "ttm_eps", "ttm_ocf",
                            "shares", "ttm_eps_growth", "eps_growth_base",
                            "eps_growth_bear", "eps_growth_bull"]
                if c in fund_all.columns]
        df = df.merge(fund_all[keep], on="ticker", how="left")
    if os.path.exists(MOAT_PATH):
        moat = pd.read_parquet(MOAT_PATH)[["ticker", "moat_rating"]]
        df = df.merge(moat, on="ticker", how="left")

    return {r["ticker"]: r for _, r in df.iterrows()}


# ---------------------------------------------------------------------------
# Per-name classification helpers
# ---------------------------------------------------------------------------
def entry_status(zone, gap):
    """AT ENTRY / ELEVATED / CHASING / EXTENDED from channel zone + gap-from-flip."""
    g = gap if pd.notna(gap) else 0
    if zone == "extended":
        return "EXTENDED"
    if g > 5:
        return "CHASING"
    if g > 2 or zone == "upper":
        return "ELEVATED"
    return "AT ENTRY"


def val_label(v):
    """Plain valuation label from PEG (preferred) or PE; None if neither."""
    peg, pe = v.get("peg"), v.get("pe")
    if peg is not None:
        return "cheap" if peg < 1 else "fair" if peg <= 2 else "expensive"
    if pe is not None:
        return "cheap" if pe < 20 else "fair" if pe <= 40 else "expensive"
    return None


_ZONE_RANK = {"lower": 2, "middle": 1, "breakdown": 0, "unknown": 0,
              "upper": -1, "extended": -3}


def _entry_rank(row):
    """Higher = better entry: high conviction + low in the channel."""
    conv = row.get("conviction_score")
    conv = float(conv) if pd.notna(conv) else 0.0
    return conv + _ZONE_RANK.get(row.get("channel_zone"), 0)


def _name_status(ticker, sig, holdings):
    """Per-ticker status dict, or None if the ticker has no signal data."""
    r = sig.get(ticker)
    if r is None:
        return {"ticker": ticker, "no_data": True, "held": holdings.get(ticker)}
    v = valuation.compute_valuation(r.get("close"), r)
    moat = int(r["moat_rating"]) if pd.notna(r.get("moat_rating")) else None
    fscore = r.get("fundamental_score")
    vlabel = val_label(v)
    # Spencer's ideal: a WIDE MOAT (4-5) business, in a future-facing secular
    # trend (the theme itself), that is CASH-FLOWING NOW at a sane price (not
    # 'expensive' on PEG/PE). theme-conviction is layered on in get_theme_status.
    fits_profile = (moat is not None and moat >= 4) and (vlabel in ("cheap", "fair"))
    return {
        "ticker": ticker,
        "no_data": False,
        "close": float(r["close"]) if pd.notna(r.get("close")) else None,
        "wl_state": r.get("wl_state"),
        "conviction_score": int(r["conviction_score"]) if pd.notna(r.get("conviction_score")) else None,
        "channel_zone": r.get("channel_zone"),
        "gap_from_flip": float(r["gap_from_flip"]) if pd.notna(r.get("gap_from_flip")) else None,
        "fundamental_score": int(fscore) if pd.notna(fscore) else None,
        "moat_rating": moat,
        "valuation": v,
        "val_label": vlabel,
        "entry_status": entry_status(r.get("channel_zone"), r.get("gap_from_flip")),
        "held": holdings.get(ticker),
        "entry_rank": _entry_rank(r),
        "fits_profile": fits_profile,
        # raw context for auto_classify / cash_deployment (one source of truth)
        "date": str(r["date"])[:10] if pd.notna(r.get("date")) else None,
        "channel_pos": float(r["channel_pos"]) if pd.notna(r.get("channel_pos")) else None,
        "high_52w": float(r["high_52w"]) if pd.notna(r.get("high_52w")) else None,
        "low_52w": float(r["low_52w"]) if pd.notna(r.get("low_52w")) else None,
        "dist_52w_high": float(r["dist_52w_high"]) if pd.notna(r.get("dist_52w_high")) else None,
        "dist_52w_low": float(r["dist_52w_low"]) if pd.notna(r.get("dist_52w_low")) else None,
        "flip_price": float(r["flip_price"]) if pd.notna(r.get("flip_price")) else None,
        "flip_date": str(r["flip_date"])[:10] if pd.notna(r.get("flip_date")) else None,
    }


# ---------------------------------------------------------------------------
# TLT regime
# ---------------------------------------------------------------------------
def tlt_regime(sig=None):
    """Current bond-market regime from TLT's Widell state."""
    sig = sig if sig is not None else _load_signals()
    r = sig.get(TLT_TICKER)
    state = r.get("wl_state") if r is not None else None
    if state == "up":
        return {"state": "up", "signal": "tailwind", "icon": "🟢",
                "label": "BOND TAILWIND — TLT up, yields falling, growth stocks supported"}
    if state == "down":
        return {"state": "down", "signal": "headwind", "icon": "🔴",
                "label": "BOND HEADWIND — TLT down, yields rising, growth stocks face valuation pressure"}
    return {"state": state or "unknown", "signal": "neutral", "icon": "🟡",
            "label": "NEUTRAL — TLT inconclusive, no strong macro signal"}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def get_theme_status():
    """Per-theme detail + TLT regime. Returns {'themes': [...], 'tlt_regime': {...}}.

    Themes sorted high→medium→low conviction. Each theme dict carries its metadata
    plus name-level status, best-in-class status, held names, gap flag, and the
    single best entry right now.
    """
    themes = load_themes()
    holdings = load_holdings()
    sig = _load_signals()

    conv_rank = {"high": 0, "medium": 1, "low": 2}
    out = []
    for tid, meta in themes.items():
        names = meta.get("names") or []
        bic = meta.get("best_in_class") or []
        name_status = [_name_status(t, sig, holdings) for t in names]
        held_names = [n["ticker"] for n in name_status if n.get("held")]

        # best entry now — only among names with signal data; skip the regime theme
        best_entry = None
        if tid != REGIME_THEME:
            candidates = [n for n in name_status if not n["no_data"]]
            if candidates:
                best = max(candidates, key=lambda n: n["entry_rank"])
                best_entry = best

        out.append({
            "id": tid,
            "name": meta.get("name", tid),
            "thesis": meta.get("thesis", ""),
            "conviction": meta.get("conviction", "medium"),
            "constraint": meta.get("constraint", ""),
            "notes": meta.get("notes", ""),
            "is_regime": tid == REGIME_THEME,
            "names": name_status,
            "best_in_class": [_name_status(t, sig, holdings) for t in bic],
            "held_names": held_names,
            "theme_gap": (tid != REGIME_THEME) and len(held_names) == 0,
            "best_entry_now": best_entry,
        })

    out.sort(key=lambda t: (conv_rank.get(t["conviction"], 1), t["name"]))
    return {"themes": out, "tlt_regime": tlt_regime(sig)}


def get_portfolio_theme_coverage():
    """Portfolio-level summary across themes (excludes the Bond_Market regime)."""
    status = get_theme_status()
    themes = [t for t in status["themes"] if not t["is_regime"]]
    holdings = load_holdings()

    covered = [t for t in themes if t["held_names"]]
    gaps    = [t for t in themes if t["theme_gap"]]
    concentrated = [t for t in themes if len(t["held_names"]) >= CONCENTRATION]

    # Holdings that don't map to ANY secular theme — "off-thesis" names worth a
    # conscious look for a thesis-driven concentrated investor.
    themed = {tk for t in themes for tk in (load_themes().get(t["id"], {}).get("names") or [])}
    unthemed = [{"ticker": tk, "note": OFF_THESIS_NOTES.get(tk, "")}
                for tk in sorted(holdings) if tk not in themed]

    return {
        "total_themes": len(themes),
        "themes_covered": len(covered),
        "gaps": [{"id": t["id"], "name": t["name"], "conviction": t["conviction"],
                  "best_entry_now": t["best_entry_now"]} for t in gaps],
        "concentrated": [{"id": t["id"], "name": t["name"],
                          "held_names": t["held_names"]} for t in concentrated],
        "unthemed_holdings": unthemed,
        "held_count": len(holdings),
        "target_min": TARGET_MIN,
        "target_max": TARGET_MAX,
        "tlt_regime": status["tlt_regime"],
    }
