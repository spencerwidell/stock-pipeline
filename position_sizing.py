"""Position sizing engine — conviction-led target weights (advisory only).

Two outputs, matching Spencer's concentrated philosophy:

  1. REBALANCE (held names) — a model target weight per current holding, normalized
     across the currently-invested %, compared to the actual holdings.yaml weight →
     ADD / TRIM / HOLD. Cash is held constant (respected as deliberate dry powder),
     so the rebalance reweights what's owned, it doesn't deploy cash.

  2. STARTERS (gap candidates) — best-in-class names in high/medium-conviction
     themes Spencer has ZERO exposure to, with a suggested starter size. Funded from
     dry powder or by trimming overweights — surfaced separately, never auto-mixed
     into the held pie.

Sizing score (the spine):
    conviction (0-10)                    primary driver
  + theme conviction bonus (high +2 / medium +1 / low 0)
  + moat bonus (5 → +2, 4 → +1)
  + valuation (cheap +1 / fair 0 / expensive -2)
  + ⭐ fits-profile bonus (+1)

This NEVER trades — it's a suggestion, not a mechanical rebalance. Reuses
theme_engine for per-name signal/quality/theme data so there's one source of truth.
"""

import holdings_io
import theme_engine

HOLDINGS_PATH = "holdings.yaml"
MAX_WEIGHT       = 15.0   # cap on any single position (%)
MIN_STARTER      = 4.0    # don't suggest a starter smaller than this (%)
MAX_STARTER      = 7.0    # keep new starters modest
ACTION_THRESHOLD = 1.5    # |target - current| beyond this → ADD / TRIM
CONV_RANK_BONUS  = {"high": 2, "medium": 1, "low": 0}


def _load_cash(path=HOLDINGS_PATH):
    """Current CASH weight (%) from holdings.yaml; 0.0 if absent."""
    return holdings_io.load_cash(path)


def _weight(w):
    try:
        return float(str(w).replace("%", "").strip())
    except (TypeError, ValueError):
        return 0.0


def _sizing_score(ns, theme_bonus):
    """Conviction-led score for one name's status dict (from theme_engine)."""
    if not ns or ns.get("no_data"):
        return 0.1
    conv = ns.get("conviction_score") or 0
    moat = ns.get("moat_rating") or 0
    moat_bonus = 2 if moat >= 5 else 1 if moat == 4 else 0
    val = {"cheap": 1, "fair": 0, "expensive": -2}.get(ns.get("val_label"), 0)
    star = 1 if ns.get("fits_profile") else 0
    return max(0.1, conv + theme_bonus + moat_bonus + val + star)


def _cap_normalize(scores, total, cap):
    """Water-fill: allocate `total` across names ∝ score, capping each at `cap`
    and redistributing the overflow to the uncapped names."""
    locked = {}
    while True:
        avail = total - sum(locked.values())
        free = {k: v for k, v in scores.items() if k not in locked}
        s = sum(free.values())
        if s <= 0 or avail <= 0:
            return {**locked, **{k: 0.0 for k in free}}
        prov = {k: free[k] / s * avail for k in free}
        newly = [k for k, v in prov.items() if v > cap + 1e-9]
        if not newly:
            return {**locked, **prov}
        for k in newly:
            locked[k] = cap


def compute_sizing():
    """Return {rebalance, starters, cash, invested, n_held, target_min, target_max}."""
    status   = theme_engine.get_theme_status()
    sig      = theme_engine._load_signals()
    holdings = theme_engine.load_holdings()           # {ticker: 'weight'} excl CASH
    held     = {t: _weight(w) for t, w in holdings.items()}
    cash     = _load_cash()

    # ticker → best theme-conviction bonus across the themes it belongs to
    theme_bonus, theme_name = {}, {}
    for th in status["themes"]:
        if th["is_regime"]:
            continue
        b = CONV_RANK_BONUS.get(th["conviction"], 0)
        for n in th["names"]:
            tk = n["ticker"]
            if b >= theme_bonus.get(tk, -1):
                theme_bonus[tk] = max(b, theme_bonus.get(tk, 0))

    def status_for(tk):
        return theme_engine._name_status(tk, sig, holdings)

    # --- 1. Rebalance held names (reweight the invested %, cash constant) ---
    held_status = {tk: status_for(tk) for tk in held}
    scores = {tk: _sizing_score(held_status[tk], theme_bonus.get(tk, 0)) for tk in held}
    invested = round(sum(held.values()), 1)
    targets = _cap_normalize(scores, invested, MAX_WEIGHT)

    rebalance = []
    for tk in held:
        tgt = round(targets.get(tk, 0.0), 1)
        cur = round(held[tk], 1)
        delta = round(tgt - cur, 1)
        action = ("ADD" if delta >= ACTION_THRESHOLD
                  else "TRIM" if delta <= -ACTION_THRESHOLD else "HOLD")
        ns = held_status[tk]
        rebalance.append({
            "ticker": tk, "current": cur, "target": tgt, "delta": delta,
            "action": action,
            "conviction": ns.get("conviction_score"),
            "moat_rating": ns.get("moat_rating"),
            "val_label": ns.get("val_label"),
            "fits_profile": bool(ns.get("fits_profile")),
        })
    rebalance.sort(key=lambda r: r["target"], reverse=True)

    # --- 2. Gap starters (best-in-class in uncovered high/medium themes) ---
    cand = {}
    for th in status["themes"]:
        if th["is_regime"] or not th["theme_gap"] or th["conviction"] == "low":
            continue
        b = CONV_RANK_BONUS.get(th["conviction"], 0)
        for n in th["best_in_class"]:
            tk = n["ticker"]
            if tk in held or n.get("no_data"):
                continue
            sc = _sizing_score(n, b)
            if tk not in cand or sc > cand[tk]["sizing_score"]:
                starter = round(min(MAX_STARTER, max(MIN_STARTER, sc * 0.6)), 1)
                cand[tk] = {
                    "ticker": tk, "theme": th["name"], "theme_conviction": th["conviction"],
                    "starter": starter, "sizing_score": round(sc, 1),
                    "conviction": n.get("conviction_score"),
                    "moat_rating": n.get("moat_rating"),
                    "val_label": n.get("val_label"),
                    "fits_profile": bool(n.get("fits_profile")),
                    "entry_status": n.get("entry_status"),
                }
    starters = sorted(cand.values(), key=lambda c: c["sizing_score"], reverse=True)[:5]

    return {
        "rebalance": rebalance,
        "starters": starters,
        "cash": cash,
        "invested": invested,
        "n_held": len(held),
        "target_min": theme_engine.TARGET_MIN,
        "target_max": theme_engine.TARGET_MAX,
    }
