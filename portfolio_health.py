"""Portfolio health check — a single roll-up of where the portfolio stands.

Aggregates the theme engine and the sizing engine into a handful of pass/warn/fail
checks plus an overall grade, so "how healthy is the portfolio right now?" is one
glance instead of reading three tabs. Advisory only — like everything else.

Checks: position count vs target band, high-conviction theme gaps, theme coverage,
concentration, off-thesis holdings, sizing drift, bond regime, dry powder.
"""

import theme_engine
import position_sizing

GOOD, WARN, BAD, INFO = "good", "warn", "bad", "info"


def _check(label, status, detail):
    return {"label": label, "status": status, "detail": detail}


def get_health():
    """Return {overall, grade, checks:[{label,status,detail}], regime}."""
    cov = theme_engine.get_portfolio_theme_coverage()
    siz = position_sizing.compute_sizing()
    checks = []

    # Position count vs target band
    n, lo, hi = cov["held_count"], cov["target_min"], cov["target_max"]
    checks.append(_check(
        "Position count",
        GOOD if lo <= n <= hi else WARN,
        f"{n} positions (target {lo}-{hi})"))

    # High-conviction theme gaps — the one that really matters
    hi_gaps = [g["name"] for g in cov["gaps"] if g["conviction"] == "high"]
    checks.append(_check(
        "High-conviction gaps",
        GOOD if not hi_gaps else BAD,
        "none" if not hi_gaps else ", ".join(hi_gaps)))

    # Overall theme coverage
    checks.append(_check(
        "Theme coverage",
        GOOD if cov["themes_covered"] >= cov["total_themes"] * 0.5 else WARN,
        f"{cov['themes_covered']} of {cov['total_themes']} themes held"))

    # Concentration (3+ in one theme)
    conc = cov["concentrated"]
    checks.append(_check(
        "Concentration",
        GOOD if not conc else WARN,
        "balanced" if not conc
        else "; ".join(f"{c['name']} ({len(c['held_names'])})" for c in conc)))

    # Off-thesis holdings
    off = [u["ticker"] for u in cov["unthemed_holdings"]]
    checks.append(_check(
        "Off-thesis holdings",
        GOOD if not off else WARN,
        "none" if not off else ", ".join(off)))

    # Sizing drift — how far holdings are from conviction-led targets
    big = [r for r in siz["rebalance"]
           if abs(r["delta"]) >= position_sizing.ACTION_THRESHOLD]
    checks.append(_check(
        "Sizing drift",
        GOOD if len(big) <= 2 else WARN,
        "on target" if not big
        else f"{len(big)} names off target ("
             + ", ".join(f"{r['ticker']} {r['delta']:+.0f}%" for r in big[:4]) + ")"))

    # Bond-market regime
    rg = cov["tlt_regime"]
    checks.append(_check(
        "Bond regime (TLT)",
        GOOD if rg["signal"] == "tailwind" else BAD if rg["signal"] == "headwind" else INFO,
        rg["signal"]))

    # Dry powder
    checks.append(_check("Dry powder", INFO, f"{siz['cash']:.0f}% cash"))

    n_bad = sum(1 for c in checks if c["status"] == BAD)
    n_warn = sum(1 for c in checks if c["status"] == WARN)
    if n_bad:
        grade, overall = BAD, "Needs attention"
    elif n_warn >= 3:
        grade, overall = WARN, "Some flags to review"
    else:
        grade, overall = GOOD, "Healthy"

    return {"overall": overall, "grade": grade, "checks": checks, "regime": rg,
            "n_bad": n_bad, "n_warn": n_warn}
