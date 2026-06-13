"""Destination Book + cash-aware Next Steps — Concentrate & Complete (Session 47).

The Destination Book is the portfolio Spencer is BUILDING TOWARD: his highest-
conviction names at full target weights (conviction water-filled to ~92%, each capped
at MAX_WEIGHT, holding a deliberate CASH_RESERVE). Every recommendation is then just
"the next step toward the destination," cash-constrained — fewer, more decisive moves
instead of a long menu:

  CORE   — earns a destination seat; target = its conviction share of the deployed book
  SELL   — a held non-core name that's low-quality (moat≤2 & fund≤2) or off-thesis
           (in no theme): a full exit, NOT a trim-to-rump. Frees cash to redeploy.
  SPEC   — a held non-core name that still has an edge (TSLA's thesis, a cheap quality
           play): KEPT under the −7% stop, outside the core targets. Let it work.
  PENDING— a just-onboarded name with no score yet: held, untouched until it scores.

The Next Steps queue walks the available cash (CASH + sell proceeds): it COMPLETES the
underweight winners first, marks what's funded NOW vs what waits until cash frees up,
and only flags a REDUCE when a name is BOTH overweight AND low-conviction (it never
nags a trim on a high-conviction winner). No overrides, no half-measures.
"""

import auto_classify
import holdings_io
import position_sizing as ps
import theme_engine

CASH_RESERVE   = 8.0   # dry powder the book always holds back (deploy to ~92%)
MIN_ADD        = 0.5   # don't surface an add smaller than this (%)
REDUCE_GAP     = 1.5   # overweight beyond this (%) can be a REDUCE …
REDUCE_CONV    = 4     # … but only on a low-conviction name (conv ≤ this); winners left alone
SELL_MOAT      = 2     # "low quality" = moat ≤ this AND …
SELL_FUND      = 2     # … fundamental ≤ this
STOP_PCT       = 0.07  # −7% stop on the speculative sleeve
WAIT_ENTRY     = ("EXTENDED", "CHASING")   # extended → wait for a pullback to add


def _dollars(pct, total):
    return round(pct / 100.0 * total) if total else None


def _entry_bonus(entry):
    return {"AT ENTRY": 2, "ELEVATED": 1}.get(entry, 0)


def compute_destination():
    """Return the Destination Book, the buckets (sell/spec/pending), and the
    cash-aware Next Steps queue. Pure read — never trades."""
    status   = theme_engine.get_theme_status()
    sig      = theme_engine._load_signals()
    holdings = holdings_io.load_positions()                 # {ticker: 'weight'} excl CASH
    held     = {t: ps._weight(w) for t, w in holdings.items()}
    cash     = holdings_io.load_cash()
    meta     = holdings_io.load_portfolio_meta()
    total    = meta["total_value"]
    tidx     = auto_classify._theme_index()
    cls_by   = {c["ticker"]: c for c in auto_classify.classify_holdings()["classifications"]}

    # theme-conviction bonus per ticker (best across its themes)
    theme_bonus = {}
    for th in status["themes"]:
        if th["is_regime"]:
            continue
        b = ps.CONV_RANK_BONUS.get(th["conviction"], 0)
        for n in th["names"]:
            theme_bonus[n["ticker"]] = max(b, theme_bonus.get(n["ticker"], 0))

    ns_by = {tk: theme_engine._name_status(tk, sig, holdings) for tk in held}

    # --- bucket every holding ------------------------------------------------
    core, spec_keep, sells, pending = {}, {}, {}, {}
    for tk, w in held.items():
        ns = ns_by[tk]
        moat, fund = ns.get("moat_rating"), ns.get("fundamental_score")
        themes = tidx.get(tk, {}).get("themes") or []
        tier = (cls_by.get(tk) or {}).get("tier")
        if ns.get("conviction_score") is None and moat is None:
            pending[tk] = w                                  # not scored yet
        elif tier == "CORE":
            core[tk] = w
        elif ((moat or 9) <= SELL_MOAT and (fund or 9) <= SELL_FUND) or not themes:
            sells[tk] = w                                    # low quality / off-thesis → exit
        else:
            spec_keep[tk] = w                                # has an edge → keep under stop

    # --- destination targets: conviction water-fill over the core book -------
    # Deploy (100 − reserve), minus the weight parked in the spec sleeve and in
    # still-unscored pending names, across the core seats; cap each at MAX_WEIGHT.
    reserved = CASH_RESERVE + sum(spec_keep.values()) + sum(pending.values())
    deploy   = max(0.0, 100.0 - reserved)
    scores   = {tk: ps._sizing_score(ns_by[tk], theme_bonus.get(tk, 0)) for tk in core}
    targets  = ps._cap_normalize(scores, deploy, ps.MAX_WEIGHT)

    book = []
    for tk in core:
        cur, tgt = round(core[tk], 1), round(targets.get(tk, 0.0), 1)
        ns = ns_by[tk]
        book.append({
            "ticker": tk, "current": cur, "target": tgt, "delta": round(tgt - cur, 1),
            "conviction": ns.get("conviction_score"), "moat_rating": ns.get("moat_rating"),
            "val_label": ns.get("val_label"), "fits_profile": bool(ns.get("fits_profile")),
            "entry_status": ns.get("entry_status"), "channel_zone": ns.get("channel_zone"),
        })
    book.sort(key=lambda r: r["target"], reverse=True)

    # --- macro gate: hold fresh buys near a CPI/FOMC print -------------------
    macro_wait, macro_label = False, None
    try:
        import macro_calendar
        evs = macro_calendar.nearby_events(ahead_days=3, back_days=0)
        if evs:
            macro_wait, macro_label = True, evs[0]["event"]
    except Exception:
        pass

    # --- tide: the top-down pacing layer. It does NOT move the destination
    # targets (those stay stable so they don't churn when the tide flips) — it
    # sets how much cash to release NOW (a bigger buffer in a falling tide) and
    # holds adds whose sector is sinking. Exits/reduces are never tide-gated.
    try:
        import tide as _tide
        tide_info = _tide.market_tide()
        sect_tides = _tide.sector_tides()
    except Exception:
        tide_info = {"level": "NEUTRAL", "reserve": CASH_RESERVE, "gate": False}
        sect_tides = {}
    tide_reserve = tide_info.get("reserve", CASH_RESERVE)
    tide_gate = tide_info.get("gate", False)

    # --- Next Steps queue ----------------------------------------------------
    actions, waitlist = [], []

    # 1) SELLs first — decisive exits that free the cash (a source, never gated)
    for tk, w in sorted(sells.items(), key=lambda kv: -kv[1]):
        ns = ns_by[tk]
        actions.append({
            "type": "SELL", "action": "SELL", "ticker": tk, "trade_pct": -round(w, 1),
            "new_weight": 0.0, "from_pct": round(w, 1), "suggested_dollars": _dollars(w, total),
            "price": ns.get("close"), "conviction": ns.get("conviction_score"),
            "priority": 100,   # always top — do these first, they fund the rest
            "detail": (f"non-core — conv {ns.get('conviction_score')}, moat "
                       f"{ns.get('moat_rating')}/5, F {ns.get('fundamental_score')}/5"
                       f"{', off-thesis' if not (tidx.get(tk, {}).get('themes')) else ''}. "
                       f"Exit and redeploy."),
        })

    # 2) REDUCE — an overweight AND low-conviction name (never a winner). Computed
    #    before the adds so its proceeds join the cash that funds them.
    reduce_proceeds = 0.0
    for b in book:
        if b["delta"] <= -REDUCE_GAP and (b["conviction"] or 99) <= REDUCE_CONV:
            cut = round(-b["delta"], 1)
            reduce_proceeds += cut
            actions.append({
                "type": "REDUCE", "action": "REDUCE", "ticker": b["ticker"],
                "trade_pct": -cut, "new_weight": b["target"], "from_pct": b["current"],
                "suggested_dollars": _dollars(cut, total), "conviction": b["conviction"],
                "priority": 50,
                "detail": (f"overweight vs conviction — held {b['current']:.0f}% but conv "
                           f"only {b['conviction']} → target {b['target']:.0f}%. Free cash "
                           f"for the winners."),
            })

    # Cash to deploy = current cash + sell proceeds + reduce proceeds, less the
    # tide-set reserve (8% neutral, ~5% rising = deploy, ~12% falling = hold powder).
    pool = round(cash + sum(sells.values()) + reduce_proceeds, 1)
    deployable = max(0.0, round(pool - tide_reserve, 1))

    # 3) COMPLETE underweight winners — ranked, walk the deployable cash
    adds = [b for b in book if b["delta"] >= MIN_ADD]
    for b in adds:
        b["_pri"] = ((b["conviction"] or 0) + theme_bonus.get(b["ticker"], 0)
                     + _entry_bonus(b["entry_status"]) + (1 if b["fits_profile"] else 0)
                     + min(b["delta"], 5) * 0.2)            # nudge the most-incomplete up
    adds.sort(key=lambda b: -b["_pri"])

    remaining = deployable
    for b in adds:
        tk = b["ticker"]
        want = b["delta"]
        extended = b["entry_status"] in WAIT_ENTRY
        tk_tide = _tide.ticker_tide(tk, sect_tides) if sect_tides else "NEUTRAL"
        sinking = tide_gate and tk_tide == "FALLING"
        item = {
            "type": "ADD", "action": "ADD", "ticker": tk, "conviction": b["conviction"],
            "price": None, "from_pct": b["current"], "target": b["target"],
            "priority": b["_pri"], "sector_tide": tk_tide,
            "detail": (f"complete to target — conv {b['conviction']}, "
                       f"{b['entry_status']}, {b['channel_zone']} channel "
                       f"(held {b['current']:.0f}% → {b['target']:.0f}%)"),
        }
        if macro_wait or extended or sinking:
            item.update({"trade_pct": round(want, 1), "new_weight": b["target"],
                         "suggested_dollars": _dollars(want, total),
                         "wait_reason": (f"hold near {macro_label}" if macro_wait
                                         else "extended — wait for a pullback" if extended
                                         else "falling tide in its sector — wait for the turn")})
            waitlist.append(item)
            continue
        if remaining < MIN_ADD:                              # out of cash → defer
            item.update({"trade_pct": round(want, 1), "new_weight": b["target"],
                         "suggested_dollars": _dollars(want, total),
                         "wait_reason": "cash committed — next when it frees up"})
            waitlist.append(item)
            continue
        fund = round(min(want, remaining), 1)                # may be a partial fill
        remaining = round(remaining - fund, 1)
        item.update({"trade_pct": fund, "new_weight": round(b["current"] + fund, 1),
                     "suggested_dollars": _dollars(fund, total),
                     "partial": fund < want - 1e-9})
        actions.append(item)

    actions.sort(key=lambda a: -a["priority"])

    invested = round(sum(held.values()), 1)
    return {
        "book": book, "sells": sells, "spec_keep": spec_keep, "pending": pending,
        "actions": actions, "waitlist": waitlist,
        "cash": cash, "pool": pool, "reserve": tide_reserve,
        "deployable": deployable, "uncommitted": round(remaining, 1),
        "invested": invested, "total_value": total,
        "n_core": len(core), "n_spec": len(spec_keep), "n_sell": len(sells),
        "macro_wait": macro_wait, "macro_label": macro_label,
        "tide": tide_info, "stop_pct": STOP_PCT,
    }


if __name__ == "__main__":
    d = compute_destination()
    print(f"Destination Book — {d['n_core']} core, deploy {sum(b['target'] for b in d['book']):.0f}%, "
          f"reserve {d['reserve']:.0f}%")
    for b in d["book"]:
        print(f"  {b['ticker']:5} {b['current']:>4.0f}% → {b['target']:>5.1f}%  ({b['delta']:+.1f})  conv {b['conviction']}")
    print(f"\nNext Steps — pool {d['pool']:.0f}% (deployable {d['deployable']:.0f}%):")
    for a in d["actions"]:
        nw = a.get("new_weight")
        print(f"  {a['action']:7} {a['ticker']:5} {a.get('trade_pct'):+}%"
              f"{' → '+format(nw,'.0f')+'%' if nw is not None else ''}  {a['detail']}")
    if d["waitlist"]:
        print("\nWhen cash frees up:")
        for w in d["waitlist"]:
            print(f"  {w['action']:7} {w['ticker']:5} +{w['trade_pct']}%  ({w.get('wait_reason')})")
    print(f"\nKeep as spec (stop): {list(d['spec_keep'])} | Pending: {list(d['pending'])}")
