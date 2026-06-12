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
import positions as positions_mod
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
GOOD_ENTRY      = ("AT ENTRY", "ELEVATED")  # acceptable entry statuses to deploy into now
MAX_WEIGHT      = 15.0
GAP_CONV        = 6
NEW_SETUP_CONV  = 8           # not-held on-thesis name at conv≥8 = a fresh setup worth acting on
WATCH_CONV      = 6           # conv 6-7 not-held = a watchlist candidate (not yet an action)
WAIT_MACRO_DAYS = 3           # a CPI/FOMC within this many days → hold fresh buys (→ watchlist)
WAIT_ENTRY      = ("EXTENDED", "CHASING")  # entry statuses that mean wait-for-pullback
STARTER_PCT     = 3.0         # default starter size for a new on-thesis setup
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
    """Consolidated, ranked, macro-aware deployment read — ONE action model.

    Every actionable item (add-to-core, new on-thesis setup, gap starter, trim/review,
    beaten-down quality) flows through one builder with a priority rank and NOW/WAIT
    timing (fresh buys WAIT near a CPI/FOMC print or when a name is extended). Returns
    `actions` (NOW, ranked, loggable), `watchlist` (WAIT + conv 6-7 approaching),
    speculative stops, thesis alerts, position-count context, and a hold-cash fallback.
    """
    cls      = auto_classify.classify_holdings()
    classifications = cls["classifications"]
    holdings = holdings_io.load_positions()
    sig      = theme_engine._load_signals()
    status   = theme_engine.get_theme_status()
    tidx     = auto_classify._theme_index()
    meta     = holdings_io.load_portfolio_meta()
    cash_pct = holdings_io.load_cash()
    total    = meta["total_value"]
    cls_by   = {c["ticker"]: c for c in classifications}
    held     = set(holdings)

    # Deterministic macro gate: a CPI/FOMC within WAIT_MACRO_DAYS holds fresh buys
    # (respect the Fed/CPI — act after the print, not into it).
    macro_wait, macro_label = False, None
    try:
        import macro_calendar
        _evs = macro_calendar.nearby_events(ahead_days=WAIT_MACRO_DAYS, back_days=0)
        if _evs:
            macro_wait, macro_label = True, _evs[0]["event"]
    except Exception:
        pass

    _TCONV_BONUS = {"high": 2, "medium": 1, "low": 0}
    items = []

    def _add(tk, typ, action, pct, detail, ns, is_buy=True, best_in=False, theme_conv=None):
        """Build one ranked, timed action item. Fresh buys WAIT near a macro print or
        when the name is extended; trims/reviews are never macro-gated."""
        entry = ns.get("entry_status")
        if is_buy and macro_wait:
            timing, wr = "WAIT", f"hold fresh buys near {macro_label}"
        elif is_buy and entry in WAIT_ENTRY:
            timing, wr = "WAIT", "wait for a pullback (extended)"
        else:
            timing, wr = "NOW", None
        conv = ns.get("conviction_score") or 0
        if is_buy:
            pr = (conv + _TCONV_BONUS.get(theme_conv, 0)
                  + (1 if ns.get("fits_profile") else 0)
                  + (2 if entry == "AT ENTRY" else 1 if entry == "ELEVATED" else 0)
                  + (1 if best_in else 0))
        else:
            pr = 9 if typ == "REVIEW" else 6      # REVIEW (thesis breaking) ranks above TRIM
        items.append({
            "ticker": tk, "type": typ, "action": action,
            "suggested_pct": pct, "suggested_dollars": _dollars(pct, total),
            "detail": detail, "price": ns.get("close"),
            "conviction": ns.get("conviction_score"), "channel_zone": ns.get("channel_zone"),
            "entry_status": entry, "tier": (cls_by.get(tk) or {}).get("tier"),
            "is_buy": is_buy, "timing": timing, "wait_reason": wr, "priority": round(pr, 1),
        })

    # 1) ADD TO CORE — a held core name on weakness or sitting at entry
    for c in classifications:
        if c["tier"] != "CORE":
            continue
        tk = c["ticker"]; ns = theme_engine._name_status(tk, sig, holdings)
        conv = ns.get("conviction_score")
        weak = ns.get("wl_state") in WEAK_STATES and ns.get("channel_zone") in WEAK_ZONES
        at_entry = ns.get("entry_status") in GOOD_ENTRY
        if conv is not None and conv >= CORE_WEAK_CONV and (weak or at_entry):
            w = _weight(holdings.get(tk)); gap = round(MAX_WEIGHT - w, 1)
            pct = gap if gap >= 0.5 else 1.5
            _add(tk, "ADD", "ADD TO CORE", pct,
                 f"core {'weakness' if weak else 'at entry'} — {ns.get('wl_state')}, "
                 f"{ns.get('channel_zone')} channel, conv {conv}/10. Held {w:.0f}%, "
                 f"toward {min(MAX_WEIGHT, w + pct):.0f}%", ns,
                 theme_conv=tidx.get(tk, {}).get("max_conv"))

    # 2) NEW SETUP — a not-held on-thesis name at conv≥8 (best-in-class breadth across
    #    secular themes IS the thesis, not dilution) + zero-exposure gap starters
    seen = set()
    for tk in tidx:
        if tk in held or tk in SECTOR_ETFS:
            continue
        ns = theme_engine._name_status(tk, sig, holdings)
        if not ns or ns.get("no_data"):
            continue
        conv = ns.get("conviction_score")
        if conv is not None and conv >= NEW_SETUP_CONV:
            ti = tidx.get(tk, {}); theme = (ti.get("themes") or ["off-thesis"])[0]
            tier = auto_classify.tier_for_new(ns, ti)
            stop = (f" · speculative → −7% stop ${round(ns['close'] * (1 - STOP_PCT), 2)}"
                    if tier == "SPECULATIVE" else "")
            _add(tk, "NEW", f"NEW SETUP ({theme})", STARTER_PCT,
                 f"conv {conv}/10, {ns.get('entry_status')}, {ns.get('channel_zone')} "
                 f"channel, moat {ns.get('moat_rating')}/5{stop}", ns,
                 best_in=True, theme_conv=ti.get("max_conv"))
            seen.add(tk)
    for th in status["themes"]:
        if th["is_regime"] or th["conviction"] != "high" or not th["theme_gap"]:
            continue
        for n in th["best_in_class"]:
            tk = n["ticker"]
            if tk in held or tk in seen or n.get("no_data"):
                continue
            conv = n.get("conviction_score"); cpos = n.get("channel_pos")
            near_low = n.get("dist_52w_low") is not None and n["dist_52w_low"] <= NEAR_LOW_GAP
            if (n.get("channel_zone") in WEAK_ZONES and conv is not None and conv >= GAP_CONV
                    and cpos is not None and cpos < NOT_EXTENDED
                    and (near_low or n.get("entry_status") == "AT ENTRY")):
                _add(tk, "NEW", f"GAP STARTER ({th['name']})", GAP_STARTER_PCT,
                     f"fills the {th['name']} gap (zero exposure) — conv {conv}/10, "
                     f"{n.get('entry_status')}, moat {n.get('moat_rating')}/5", n,
                     best_in=True, theme_conv="high")
                seen.add(tk)

    # 3) TRIM / REVIEW — a held name that's extended (trim into strength) or breaking
    #    down (reassess the thesis). Not a buy, so never macro-gated.
    for c in classifications:
        tk = c["ticker"]; ns = theme_engine._name_status(tk, sig, holdings)
        st, reason = positions_mod.assess_position(ns.get("channel_zone"), ns.get("wl_state"))
        if st in ("TRIM", "REVIEW"):
            w = _weight(holdings.get(tk)); pct = round(min(max(w * 0.3, 1.0), 3.0), 1)
            _add(tk, st, st, pct, (reason or st) + f" — held {w:.0f}%, trim ~{pct:.0f}%",
                 ns, is_buy=False)

    # 4) BEATEN-DOWN QUALITY — a non-held quality name near its low, not a falling knife
    for tk in tidx:
        if tk in held or tk in SECTOR_ETFS or tk in seen:
            continue
        ns = theme_engine._name_status(tk, sig, holdings)
        if not ns or ns.get("no_data"):
            continue
        moat, fund = ns.get("moat_rating"), ns.get("fundamental_score")
        if (ns.get("dist_52w_low") is not None and ns["dist_52w_low"] <= BEATEN_LOW_GAP
                and moat is not None and moat >= 3 and fund is not None and fund >= 3
                and ns.get("wl_state") != "down" and ns.get("channel_zone") in BEATEN_ZONES):
            stop = round(ns["close"] * (1 - STOP_PCT), 2)
            _add(tk, "BEATEN", "BEATEN-DOWN QUALITY", BEATEN_PCT,
                 f"near 52-wk low ({ns['dist_52w_low']:.0f}% above), moat {moat}/5, "
                 f"F {fund}/5, {ns.get('wl_state')} — speculative → −7% stop ${stop}", ns,
                 theme_conv=tidx.get(tk, {}).get("max_conv"))
            seen.add(tk)

    actions    = sorted([i for i in items if i["timing"] == "NOW"], key=lambda i: -i["priority"])
    wait_items = sorted([i for i in items if i["timing"] == "WAIT"], key=lambda i: -i["priority"])

    # Watchlist = WAIT-timed actions + conv 6-7 not-held "approaching" candidates.
    watch_seen = {i["ticker"] for i in items}
    approaching = []
    for tk in tidx:
        if tk in held or tk in SECTOR_ETFS or tk in watch_seen:
            continue
        ns = theme_engine._name_status(tk, sig, holdings)
        conv = ns.get("conviction_score") if ns else None
        if (conv is not None and WATCH_CONV <= conv < NEW_SETUP_CONV
                and not ns.get("no_data")):
            ti = tidx.get(tk, {}); theme = (ti.get("themes") or ["off-thesis"])[0]
            approaching.append({
                "ticker": tk, "type": "WATCH", "conviction": conv,
                "entry_status": ns.get("entry_status"), "channel_zone": ns.get("channel_zone"),
                "priority": conv + _TCONV_BONUS.get(ti.get("max_conv"), 0),
                "detail": f"approaching — conv {conv}/10, {ns.get('entry_status')}, "
                          f"{ns.get('channel_zone')} channel ({theme})",
            })
    approaching.sort(key=lambda w: -w["priority"])
    watchlist = wait_items + approaching

    hold_cash = None
    if not actions:
        hold_cash = {
            "message": "No compelling entries right now — hold cash, patience is the edge.",
            "triggers": [{"ticker": w["ticker"], "detail": w["detail"]}
                         for w in watchlist[:3]],
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
        "n_positions": len(classifications),
        "target_min": theme_engine.TARGET_MIN,
        "target_max": theme_engine.TARGET_MAX,
        "macro_wait": macro_wait,
        "macro_label": macro_label,
        "actions": actions,
        "watchlist": watchlist,
        "hold_cash": hold_cash,
        "stops": stops,
        "stops_watch": [s for s in stops if s["status"] in ("watch", "triggered")],
        "thesis_alerts": alerts,
        "classifications": classifications,
    }


if __name__ == "__main__":
    d = deployment()
    print(f"CASH {d['cash_pct']:.0f}% (${d['cash_dollars']:,}) · "
          f"CORE {d['n_core']} · SPEC {d['n_speculative']} · "
          f"{d['n_positions']} positions (target {d['target_min']}-{d['target_max']})"
          + (f" · ⏸ macro WAIT: {d['macro_label']}" if d["macro_wait"] else ""))
    print("=" * 70, "\n🎯 PORTFOLIO ACTION (NOW, ranked):")
    if d["actions"]:
        for a in d["actions"]:
            dol = f" (~${a['suggested_dollars']:,})" if a["suggested_dollars"] else ""
            print(f"  [{a['priority']:>4}] {a['action']} {a['ticker']} "
                  f"+{a['suggested_pct']}%{dol}\n          {a['detail']}")
    else:
        print("  " + d["hold_cash"]["message"])
    print("\n👀 WATCHLIST:")
    for w in d["watchlist"]:
        wr = f" [WAIT: {w.get('wait_reason')}]" if w.get("wait_reason") else ""
        lbl = w.get("action", "WATCH")
        print(f"  {lbl} {w['ticker']}{wr} — {w['detail']}")
    if d["stops_watch"]:
        print("-" * 70, "\nSPECULATIVE STOPS:")
        for s in d["stops_watch"]:
            print(f"   {s['ticker']} {s['status'].upper()} — ${s['current']} vs "
                  f"stop ${s['stop']} ({s['dist_to_stop_pct']}% away)")
    if d["thesis_alerts"]:
        print("-" * 70, "\nTHESIS INTEGRITY:")
        for a in d["thesis_alerts"]:
            print(f"   ⚠️ {a['ticker']}: {a['detail']}")
