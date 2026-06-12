"""Cash-deployment engine — "where does my next dollar go?"

Priority-ordered, advisory only (never trades). Reuses theme_engine + auto_classify
so signals, quality, themes, and tiering are one source of truth.

  STEP 1  Add to CORE on weakness — a core holding the market is offering cheaper
          (Widell rolled to inconclusive/down, dropped into the lower/middle channel)
          but whose conviction is still high. Core weakness is a BUY signal.
  STEP 2  Fill a high-conviction theme GAP at entry — best-in-class name in a
          high-conviction theme we have zero exposure to, trading at a real entry.
  STEP 3  Beaten-down QUALITY (speculative) — a non-held quality name near its
          52-wk low that isn't a falling knife. Always speculative → −7% stop.
  STEP 4  Hold cash — if nothing qualifies, say so, and show exactly what WOULD
          need to happen (the trigger price) for steps 1–3 to fire. Patience is edge.

Stop tracking (SPECULATIVE only — CORE is never stopped): entry price is anchored
the first date a ticker is seen in holdings, persisted in data/positions_seen.json
(system-maintained, not hand-edited). Thesis-integrity watches CORE names for a
≥2-point fundamental drop vs the last recorded reading.
"""

import json
import os

import auto_classify
import holdings_io
import theme_engine

try:
    from sector_map import SECTOR_ETFS
except Exception:                       # pragma: no cover - defensive
    SECTOR_ETFS = []

SEEN_PATH = "data/positions_seen.json"

# Tunables (documented inline above)
CORE_WEAK_CONV  = 5   # Session 40 conviction re-weight: a down-state core name in a
                      # good channel now tops out ~5-6 (Widell state is weighted 4, so
                      # "weakness" caps state points), so 5 keeps catching quality core
                      # pullbacks; ≥6 would require a recent flip on top.
WEAK_STATES     = ("inconclusive", "down")
WEAK_ZONES      = ("lower", "middle")
MAX_WEIGHT      = 15.0
GAP_CONV        = 6
NOT_EXTENDED    = 0.8          # channel_pos below this = not extended
NEAR_LOW_GAP    = 10.0         # within 10% of 52-wk low (step 2)
BEATEN_LOW_GAP  = 15.0         # within 15% of 52-wk low (step 3)
BEATEN_ZONES    = ("lower", "breakdown")
GAP_STARTER_PCT = 3.0
BEATEN_PCT      = 2.5
STOP_PCT        = 0.07         # −7% stop on speculative positions
STOP_WARN_PCT   = 2.0          # within this % of the stop → watch


# ---------------------------------------------------------------------------
# Persistence — entry-price anchor + last-seen fundamentals (system-maintained)
# ---------------------------------------------------------------------------
def _load_seen(path=SEEN_PATH):
    if not os.path.exists(path):
        return {}
    try:
        with open(path) as f:
            return json.load(f) or {}
    except Exception:
        return {}


def _save_seen(seen, path=SEEN_PATH):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        json.dump(seen, f, indent=2, sort_keys=True)


def record_positions(sig=None, path=SEEN_PATH):
    """Write path (call once at pipeline close). Adds newly-seen holdings with an
    entry-price anchor, prunes sold names, refreshes last-seen fundamentals/moat.

    Returns the thesis-integrity alerts detected BEFORE refreshing (so a ≥2-pt
    fundamental drop is caught on the transition, then the baseline moves on).
    """
    sig      = sig if sig is not None else theme_engine._load_signals()
    holdings = holdings_io.load_positions()
    seen     = _load_seen(path)

    alerts = thesis_integrity_alerts(sig=sig, seen=seen)   # compare vs old baseline

    held = set(holdings)
    for tk in list(seen):                                   # prune sold names
        if tk not in held:
            del seen[tk]

    for tk in holdings:
        ns = theme_engine._name_status(tk, sig, holdings)
        if not ns or ns.get("no_data"):
            continue
        rec = seen.setdefault(tk, {})
        if "entry_price" not in rec:                        # first time seen
            rec["first_seen"]  = ns.get("date")
            rec["entry_price"] = ns.get("close")
        rec["last_fundamental"] = ns.get("fundamental_score")
        rec["last_moat"]        = ns.get("moat_rating")
    _save_seen(seen, path)
    return alerts


# ---------------------------------------------------------------------------
# Thesis integrity (read-only) — CORE names whose evidence has eroded
# ---------------------------------------------------------------------------
def thesis_integrity_alerts(classifications=None, sig=None, seen=None):
    """CORE holdings whose fundamental score dropped ≥2 points (or moat dropped)
    vs the last recorded reading. Read-only; safe to call from the dashboard."""
    if classifications is None:
        classifications = auto_classify.classify_holdings()["classifications"]
    sig  = sig if sig is not None else theme_engine._load_signals()
    seen = seen if seen is not None else _load_seen()
    holdings = holdings_io.load_positions()

    out = []
    for c in classifications:
        if c["tier"] != "CORE":
            continue
        tk  = c["ticker"]
        rec = seen.get(tk)
        if not rec:
            continue
        ns = theme_engine._name_status(tk, sig, holdings)
        cur_f, old_f = ns.get("fundamental_score"), rec.get("last_fundamental")
        cur_m, old_m = ns.get("moat_rating"), rec.get("last_moat")
        if cur_f is not None and old_f is not None and cur_f <= old_f - 2:
            out.append({"ticker": tk, "kind": "fundamental",
                        "detail": f"F score {old_f}→{cur_f} (−{old_f - cur_f}) — review thesis"})
        elif cur_m is not None and old_m is not None and cur_m <= old_m - 1:
            out.append({"ticker": tk, "kind": "moat",
                        "detail": f"moat {old_m}→{cur_m} — review thesis"})
    return out


# ---------------------------------------------------------------------------
# Stop tracking (SPECULATIVE only)
# ---------------------------------------------------------------------------
def speculative_stops(classifications=None, sig=None, seen=None):
    """Per speculative holding: entry, current, −7% stop, distance, and a status
    of ok / watch (within 2% of stop) / triggered (at or below stop)."""
    if classifications is None:
        classifications = auto_classify.classify_holdings()["classifications"]
    sig  = sig if sig is not None else theme_engine._load_signals()
    seen = seen if seen is not None else _load_seen()
    holdings = holdings_io.load_positions()

    rows = []
    for c in classifications:
        if c["tier"] != "SPECULATIVE":
            continue
        tk = c["ticker"]
        ns = theme_engine._name_status(tk, sig, holdings)
        cur = ns.get("close")
        entry = (seen.get(tk) or {}).get("entry_price")
        if entry is None:                       # not recorded yet → anchor at current
            entry = cur
        if cur is None or entry is None or entry <= 0:
            continue
        stop = round(entry * (1 - STOP_PCT), 2)
        dist = round((cur / stop - 1) * 100, 1)  # % the price sits above the stop
        status = ("triggered" if cur <= stop
                  else "watch" if dist <= STOP_WARN_PCT else "ok")
        rows.append({"ticker": tk, "entry": round(entry, 2), "current": round(cur, 2),
                     "stop": stop, "dist_to_stop_pct": dist, "status": status,
                     "weight": _weight(holdings.get(tk))})
    rows.sort(key=lambda r: r["dist_to_stop_pct"])
    return rows


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _weight(w):
    try:
        return float(str(w).replace("%", "").strip())
    except (TypeError, ValueError):
        return 0.0


def _dollars(pct, total_value):
    return round(pct / 100.0 * total_value) if total_value else None


# ---------------------------------------------------------------------------
# The engine
# ---------------------------------------------------------------------------
def deployment():
    """Full deployment read. Returns classification, priority actions (steps 1–3),
    a hold-cash fallback with trigger prices (step 4), speculative stops, thesis
    alerts, and dollar context."""
    cls      = auto_classify.classify_holdings()
    classifications = cls["classifications"]
    holdings = holdings_io.load_positions()
    sig      = theme_engine._load_signals()
    status   = theme_engine.get_theme_status()
    tidx     = auto_classify._theme_index()
    meta     = holdings_io.load_portfolio_meta()
    cash_pct = holdings_io.load_cash()
    total    = meta["total_value"]

    actions = []

    # --- STEP 1: add to CORE on weakness ---
    for c in classifications:
        if c["tier"] != "CORE":
            continue
        tk = c["ticker"]
        ns = theme_engine._name_status(tk, sig, holdings)
        conv = ns.get("conviction_score")
        if (ns.get("wl_state") in WEAK_STATES and ns.get("channel_zone") in WEAK_ZONES
                and conv is not None and conv >= CORE_WEAK_CONV):
            w = _weight(holdings.get(tk))
            gap = round(MAX_WEIGHT - w, 1)
            add_pct = gap if gap >= 0.5 else 1.5      # under target → toward 15; else top-up
            staged = " (stage in tranches)" if add_pct > 2 else ""
            actions.append({
                "step": 1, "ticker": tk, "tier": "CORE", "action": "ADD TO CORE",
                "suggested_pct": add_pct, "suggested_dollars": _dollars(add_pct, total),
                "detail": (f"core weakness — {ns.get('wl_state')}, {ns.get('channel_zone')} "
                           f"channel, conv {conv}/10. Held {w:.0f}%, add toward "
                           f"{min(MAX_WEIGHT, w + add_pct):.0f}%{staged}"),
                "price": ns.get("close"), "conviction": conv,
                "channel_zone": ns.get("channel_zone"),
            })

    # --- STEP 2: high-conviction theme gap at entry ---
    for th in status["themes"]:
        if th["is_regime"] or th["conviction"] != "high" or not th["theme_gap"]:
            continue
        for n in th["best_in_class"]:
            if n.get("no_data") or n.get("ticker") in holdings:
                continue
            conv = n.get("conviction_score")
            cpos = n.get("channel_pos")
            near_low = (n.get("dist_52w_low") is not None and n["dist_52w_low"] <= NEAR_LOW_GAP)
            at_pullback = n.get("entry_status") == "AT ENTRY"
            if (n.get("channel_zone") in WEAK_ZONES and conv is not None and conv >= GAP_CONV
                    and cpos is not None and cpos < NOT_EXTENDED and (near_low or at_pullback)):
                tier = auto_classify.tier_for_new(n, tidx.get(n["ticker"]))
                stop_note = (f" · speculative → −7% stop at "
                             f"${round(n['close'] * (1 - STOP_PCT), 2)}"
                             if tier == "SPECULATIVE" else "")
                actions.append({
                    "step": 2, "ticker": n["ticker"], "tier": tier,
                    "action": f"GAP STARTER ({th['name']})",
                    "suggested_pct": GAP_STARTER_PCT,
                    "suggested_dollars": _dollars(GAP_STARTER_PCT, total),
                    "detail": (f"fills the {th['name']} gap at entry — {n['entry_status']}, "
                               f"{n.get('channel_zone')} channel, conv {conv}/10, "
                               f"moat {n.get('moat_rating')}/5{stop_note}"),
                    "price": n.get("close"), "conviction": conv,
                    "channel_zone": n.get("channel_zone"),
                })

    # --- STEP 3: beaten-down quality (speculative), not held ---
    themed = set(tidx)                                  # single names that map to a theme
    for tk in themed:
        if tk in holdings or tk in SECTOR_ETFS:
            continue
        ns = theme_engine._name_status(tk, sig, holdings)
        if not ns or ns.get("no_data"):
            continue
        moat, fund = ns.get("moat_rating"), ns.get("fundamental_score")
        if (ns.get("dist_52w_low") is not None and ns["dist_52w_low"] <= BEATEN_LOW_GAP
                and moat is not None and moat >= 3 and fund is not None and fund >= 3
                and ns.get("wl_state") != "down" and ns.get("channel_zone") in BEATEN_ZONES):
            if any(a["ticker"] == tk for a in actions):   # already surfaced in step 2
                continue
            stop = round(ns["close"] * (1 - STOP_PCT), 2)
            actions.append({
                "step": 3, "ticker": tk, "tier": "SPECULATIVE",
                "action": "BEATEN-DOWN QUALITY",
                "suggested_pct": BEATEN_PCT, "suggested_dollars": _dollars(BEATEN_PCT, total),
                "detail": (f"near 52-wk low ({ns['dist_52w_low']:.0f}% above), moat "
                           f"{moat}/5, F {fund}/5, {ns.get('wl_state')}, "
                           f"{ns.get('channel_zone')} — speculative → −7% stop at ${stop}"),
                "price": ns.get("close"), "conviction": ns.get("conviction_score"),
                "channel_zone": ns.get("channel_zone"),
            })

    actions.sort(key=lambda a: (a["step"], -(a["conviction"] or 0)))

    # --- STEP 4: hold cash + what would need to happen ---
    hold_cash = None
    if not actions:
        triggers = []
        for th in status["themes"]:
            if th["is_regime"] or th["conviction"] != "high" or not th["theme_gap"]:
                continue
            be = th.get("best_entry_now")
            if not be or be.get("no_data"):
                continue
            low = be.get("low_52w")
            pull_to = round(low * (1 + NEAR_LOW_GAP / 100.0), 2) if low else None
            blocks = []
            conv = be.get("conviction_score")
            if conv is None or conv < GAP_CONV:
                blocks.append(f"conviction {conv}/10 (need ≥{GAP_CONV})")
            if be.get("channel_zone") not in WEAK_ZONES:
                blocks.append(f"{be.get('channel_zone')} channel (need lower/middle)")
            price_hint = (f" — pull back from ${be.get('close'):.0f} toward ${pull_to:.0f}"
                          if pull_to and be.get("close") else "")
            triggers.append({
                "theme": th["name"], "ticker": be["ticker"],
                "detail": (f"{be['ticker']} ({th['name']}): "
                           + ("; ".join(blocks) if blocks else "watching for entry")
                           + price_hint),
            })
        hold_cash = {
            "message": "No compelling entries. Hold cash. Patience is the edge.",
            "triggers": triggers,
        }

    stops  = speculative_stops(classifications, sig)
    alerts = thesis_integrity_alerts(classifications, sig)

    return {
        "cash_pct": cash_pct,
        "cash_dollars": _dollars(cash_pct, total),
        "total_value": total,
        "bi_weekly_contribution": meta["bi_weekly_contribution"],
        "n_core": len(cls["core"]),
        "n_speculative": len(cls["speculative"]),
        "actions": actions,
        "hold_cash": hold_cash,
        "stops": stops,
        "stops_watch": [s for s in stops if s["status"] in ("watch", "triggered")],
        "thesis_alerts": alerts,
        "classifications": classifications,
    }


if __name__ == "__main__":
    d = deployment()
    print(f"CASH {d['cash_pct']:.0f}% (${d['cash_dollars']:,}) · "
          f"CORE {d['n_core']} · SPEC {d['n_speculative']}")
    print("=" * 70)
    if d["actions"]:
        for a in d["actions"]:
            dol = f" (~${a['suggested_dollars']:,})" if a["suggested_dollars"] else ""
            print(f"[STEP {a['step']}] {a['action']} {a['ticker']} "
                  f"+{a['suggested_pct']}%{dol}")
            print(f"          {a['detail']}")
    else:
        print(d["hold_cash"]["message"])
        for t in d["hold_cash"]["triggers"]:
            print(f"   · {t['detail']}")
    if d["stops_watch"]:
        print("-" * 70, "\nSPECULATIVE STOPS:")
        for s in d["stops_watch"]:
            print(f"   {s['ticker']} {s['status'].upper()} — ${s['current']} vs "
                  f"stop ${s['stop']} ({s['dist_to_stop_pct']}% away)")
    if d["thesis_alerts"]:
        print("-" * 70, "\nTHESIS INTEGRITY:")
        for a in d["thesis_alerts"]:
            print(f"   ⚠️ {a['ticker']}: {a['detail']}")
