"""Market Tide — the top-down regime that scales how aggressively to deploy.

"A rising tide lifts all boats; a falling tide smashes them. Don't fight the tide."

The Tide is a single read on market direction, fused from three things already in the
pipeline:

  • the broad benchmarks — SPY / QQQ / IWM Widell state (the ocean)
  • sector breadth — how many sector/thematic ETFs are up vs down (the boats)
  • the TLT bond regime — macro tailwind / headwind (the wind)

It outputs RISING / NEUTRAL / FALLING plus a deployment posture: in a rising tide the
Destination Book deploys aggressively (small cash reserve); in a falling tide it holds
more powder and won't chase adds into the downtrend — it waits for the turn. Per-sector
tides let a name in a still-rising sector keep its tailwind even when the market is soft.

Pure read off data/stock_vsa.parquet — never trades.
"""

import os

import pandas as pd

import theme_engine
from sector_map import SECTOR_ETFS, get_parent_etfs

VSA_PATH    = "data/stock_vsa.parquet"
BENCHMARKS  = ["SPY", "QQQ", "IWM"]          # the ocean — broad market direction
_NOT_SECTOR = set(BENCHMARKS) | {"TLT"}      # excluded from the sector-breadth count

# Cash reserve the Destination Book holds back, by tide (Spencer's 8% is NEUTRAL):
RESERVE_BY_TIDE = {"RISING": 5.0, "NEUTRAL": 8.0, "FALLING": 12.0}
_STATE_VAL = {"up": 1, "inconclusive": 0, "down": -1}
_ICON      = {"RISING": "🌊🟢", "NEUTRAL": "🌊🟡", "FALLING": "🌊🔴"}


def _latest(path=VSA_PATH):
    if not os.path.exists(path):
        return None
    df = pd.read_parquet(path)
    return df.sort_values("date").groupby("ticker", as_index=False).tail(1).set_index("ticker")


def _level(state):
    """A single ETF's tide from its Widell state."""
    return {"up": "RISING", "down": "FALLING"}.get(state, "NEUTRAL")


def sector_tides(latest=None):
    """{etf: {'level','state','channel_zone','channel_pos'}} for every sector ETF."""
    latest = _latest() if latest is None else latest
    out = {}
    if latest is None:
        return out
    for e in SECTOR_ETFS:
        if e not in latest.index:
            continue
        r = latest.loc[e]
        out[e] = {
            "level": _level(r.get("wl_state")),
            "state": r.get("wl_state"),
            "channel_zone": r.get("channel_zone"),
            "channel_pos": float(r["channel_pos"]) if pd.notna(r.get("channel_pos")) else None,
        }
    return out


def ticker_tide(ticker, sect=None):
    """The tide for a name's parent sector(s) — the best (most favorable) of them.
    RISING if any parent sector is rising, else NEUTRAL, else FALLING. Unknown → NEUTRAL."""
    sect = sector_tides() if sect is None else sect
    levels = [sect[e]["level"] for e in get_parent_etfs(ticker) if e in sect]
    if not levels:
        return "NEUTRAL"
    if "RISING" in levels:
        return "RISING"
    if "NEUTRAL" in levels:
        return "NEUTRAL"
    return "FALLING"


def market_tide(latest=None):
    """The overall tide. Returns level, score, reserve, posture, and the inputs."""
    latest = _latest() if latest is None else latest
    if latest is None:
        return {"level": "NEUTRAL", "score": 0.0, "reserve": RESERVE_BY_TIDE["NEUTRAL"],
                "icon": _ICON["NEUTRAL"], "label": "Tide unknown — no signal data",
                "posture": "Deploy at your neutral pace.", "gate": False,
                "breadth": {}, "benchmarks": {}, "tlt": None}

    # 1) benchmarks — the ocean
    bench = {b: latest.loc[b, "wl_state"] for b in BENCHMARKS if b in latest.index}
    bench_avg = (sum(_STATE_VAL.get(s, 0) for s in bench.values()) / len(bench)
                 if bench else 0.0)

    # 2) sector breadth — the boats
    sect = sector_tides(latest)
    sectors = {e: v for e, v in sect.items() if e not in _NOT_SECTOR}
    n = len(sectors) or 1
    n_up   = sum(1 for v in sectors.values() if v["level"] == "RISING")
    n_down = sum(1 for v in sectors.values() if v["level"] == "FALLING")
    breadth = (n_up - n_down) / n

    # 3) TLT — the wind
    tlt = theme_engine.tlt_regime()
    tlt_mod = {"tailwind": 1, "headwind": -1}.get(tlt.get("signal"), 0)

    score = round(0.50 * bench_avg + 0.35 * breadth + 0.15 * tlt_mod, 3)
    level = "RISING" if score >= 0.15 else "FALLING" if score <= -0.15 else "NEUTRAL"

    posture = {
        "RISING":  "Tide is with you — deploy to target, complete the winners, keep little idle.",
        "NEUTRAL": "Mixed tide — deploy at your normal pace into good entries.",
        "FALLING": "Tide is against you — hold powder, don't chase adds into the downtrend; "
                   "exits and reduces still go. Wait for the turn.",
    }[level]

    return {
        "level": level, "score": score, "reserve": RESERVE_BY_TIDE[level],
        "icon": _ICON[level], "gate": level == "FALLING",
        "label": f"{level} tide — {n_up} sectors up / {n_down} down, "
                 f"benchmarks {'/'.join(f'{b}:{s}' for b, s in bench.items())}, "
                 f"bonds {tlt.get('signal', 'n/a')}",
        "posture": posture,
        "breadth": {"up": n_up, "down": n_down, "neutral": n - n_up - n_down, "total": n},
        "benchmarks": bench, "tlt": tlt,
    }


if __name__ == "__main__":
    t = market_tide()
    print(f"{t['icon']} {t['level']}  (score {t['score']})")
    print(f"  {t['label']}")
    print(f"  reserve → {t['reserve']:.0f}%  ·  {t['posture']}")
    print("\nSector tides:")
    for e, v in sorted(sector_tides().items(), key=lambda kv: kv[1]["level"]):
        print(f"  {e:5} {v['level']:8} ({v['state']}, {v['channel_zone']})")
