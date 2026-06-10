"""Sector rotation scanner.

Section A — rank the sector/thematic ETFs by opportunity (room to run vs
            extended) using Widell state + regression channel position.
Section B — within the ETFs that look favorable, find constituent stocks that
            haven't moved yet but should catch up: either more room to run than
            their sector, or lagging the sector's momentum. Quality-filtered to
            fundamental score >= 3.

Run after the daily pipeline (needs data/stock_vsa.parquet up to date).
"""

import os
import pandas as pd

from sector_map import SECTOR_ETFS, get_constituents

VSA_PATH  = "data/stock_vsa.parquet"
FUND_PATH = "data/fundamentals.parquet"

STATE_ICON = {"up": "🟢", "inconclusive": "🟡", "down": "🔴"}
STATE_RANK = {"up": 0, "inconclusive": 1, "down": 2}
MIN_FUND = 3  # quality filter for Section B


# ---------------------------------------------------------------------------
# Load most-recent bar per ticker + fundamentals
# ---------------------------------------------------------------------------
def load_latest():
    df = pd.read_parquet(VSA_PATH)
    latest = df.sort_values("date").groupby("ticker", as_index=False).tail(1)
    latest = latest[[
        "ticker", "date", "close", "wl_state", "wl_flip",
        "composite", "channel_zone", "channel_pos",
    ]].reset_index(drop=True)

    if os.path.exists(FUND_PATH):
        fund = pd.read_parquet(FUND_PATH)[["ticker", "fundamental_score"]]
        latest = latest.merge(fund, on="ticker", how="left")
    else:
        latest["fundamental_score"] = pd.NA
    return latest


# ---------------------------------------------------------------------------
# Section A — ETF / sector ranking
# ---------------------------------------------------------------------------
def section_a(latest):
    print("=" * 78)
    print("SECTION A — Sector/Thematic ETF Ranking")
    print("Best opportunity (favorable state + lower channel) at top")
    print("=" * 78)

    etf = latest[latest["ticker"].isin(SECTOR_ETFS)].copy()
    etf["state_rank"] = etf["wl_state"].map(STATE_RANK).fillna(3)
    # favorable state first, then lowest channel position (most room to run)
    etf = etf.sort_values(["state_rank", "channel_pos"],
                          na_position="last").reset_index(drop=True)

    print(f"\n{'ETF':<6} {'State':<14} {'Scr':>4} {'Zone':<9} {'ChPos':>7}")
    print("-" * 78)
    for _, r in etf.iterrows():
        icon = STATE_ICON.get(r["wl_state"], "?")
        cp   = f"{r['channel_pos']:.3f}" if pd.notna(r["channel_pos"]) else "  n/a"
        print(f"{r['ticker']:<6} {icon} {str(r['wl_state']):<11} "
              f"{int(r['composite']):>4} {str(r['channel_zone']):<9} {cp:>7}")
    return etf


# ---------------------------------------------------------------------------
# Section B — constituent laggard scan
# ---------------------------------------------------------------------------
def section_b(latest, etf_ranked):
    print("\n" + "=" * 78)
    print("SECTION B — Constituent Laggard Scan")
    print(f"ETFs in UP state or LOWER/MIDDLE zone | constituents with F >= {MIN_FUND}")
    print("=" * 78)

    by_ticker = latest.set_index("ticker")

    # ETFs worth drilling into: up state OR lower/middle channel zone
    favorable = etf_ranked[
        (etf_ranked["wl_state"] == "up")
        | (etf_ranked["channel_zone"].isin(["lower", "middle"]))
    ]

    any_hits = False
    for _, e in favorable.iterrows():
        etf_tkr   = e["ticker"]
        etf_state = e["wl_state"]
        etf_cpos  = e["channel_pos"]

        rows = []
        for stock in get_constituents(etf_tkr):
            if stock not in by_ticker.index:
                continue
            s = by_ticker.loc[stock]
            f_score = s["fundamental_score"]
            s_cpos  = s["channel_pos"]
            s_state = s["wl_state"]

            # quality filter
            if pd.isna(f_score) or f_score < MIN_FUND:
                continue

            # qualify: more room to run than sector, OR lagging sector momentum
            room_to_run = pd.notna(s_cpos) and pd.notna(etf_cpos) and s_cpos < etf_cpos
            lagging = etf_state == "up" and s_state in ("inconclusive", "down")
            if not (room_to_run or lagging):
                continue

            if room_to_run and lagging:
                reason = "BOTH"
            elif room_to_run:
                reason = "ROOM_TO_RUN"
            else:
                reason = "LAGGING"
            rows.append({
                "ticker": stock, "state": s_state, "composite": s["composite"],
                "zone": s["channel_zone"], "channel_pos": s_cpos,
                "fund": int(f_score), "reason": reason,
            })

        if not rows:
            continue

        any_hits = True
        # sort ascending by channel_pos (lowest first = most room to run)
        rows = sorted(rows, key=lambda r: (r["channel_pos"] is None,
                                           r["channel_pos"] if r["channel_pos"] is not None else 0))
        eicon = STATE_ICON.get(etf_state, "?")
        ecp   = f"{etf_cpos:.3f}" if pd.notna(etf_cpos) else "n/a"
        print(f"\n▸ {etf_tkr}  {eicon} {etf_state}  zone={e['channel_zone']}  ChPos={ecp}")
        print(f"  {'Stock':<6} {'State':<14} {'Scr':>4} {'Zone':<9} "
              f"{'ChPos':>7} {'F':>2}  Why")
        print("  " + "-" * 62)
        for r in rows:
            icon = STATE_ICON.get(r["state"], "?")
            cp   = f"{r['channel_pos']:.3f}" if pd.notna(r["channel_pos"]) else "  n/a"
            print(f"  {r['ticker']:<6} {icon} {str(r['state']):<11} "
                  f"{int(r['composite']):>4} {str(r['zone']):<9} "
                  f"{cp:>7} {r['fund']:>2}  {r['reason']}")

    if not any_hits:
        print("\n  No qualifying constituents today.")


def main():
    latest = load_latest()
    print(f"Sector Rotation — data as of {latest['date'].max().date()}  "
          f"({latest['ticker'].nunique()} tickers)\n")
    etf_ranked = section_a(latest)
    section_b(latest, etf_ranked)
    print("\nLegend: ROOM_TO_RUN=stock channel below sector | "
          "LAGGING=stock state weaker than up sector | BOTH=both")


if __name__ == "__main__":
    main()
