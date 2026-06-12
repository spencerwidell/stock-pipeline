"""Conviction score (0-10) — adds a `conviction_score` column to stock_vsa.parquet.

Blends swing state, entry-zone quality, fundamental quality, and flip freshness
into a single 0-10 "how much conviction does a buy here deserve" number.

Components (re-weighted Session 40 — backtest-driven):
  Widell state     (0-4)  up=4 inconclusive=2 down=0
  Channel position (0-3)  middle=3 lower=3 upper=1 unknown=1 breakdown=0 extended=0
  Fundamentals     (0-2)  F5=2 F4=1 F3=1 F0-2 / missing=0
  Flip recency     (0-1)  flipped within last 5 bars=1 else=0

Score 8+ = highest-conviction buy zone.

Why this weighting (see docs/CONVICTION_BACKTEST.md): the prior scheme rewarded
beaten-down names (channel lower=4, breakdown=2) and under-weighted the *validated*
Widell-state edge, which made the mid-scale carry beaten-down beta rather than signal
(0-3 bucket beat 4-5/6-7). The re-weight (a) makes the Widell state the top driver —
so ≥8 requires confirmed up-momentum, which is exactly where the forward-alpha edge
lives, (b) stops rewarding breakdowns/extended, and (c) lightens the lookahead-prone
fundamental component (3→2 pts). Result: monotonic buckets, a stronger Spearman, and a
≥8 bucket that beats the rest in nearly every year incl. the 2022 bear (+13.7% 20d).

Run AFTER composite_score.py (needs channel_zone, wl_state, wl_flip) and after
fetch_fundamentals.py (for fundamental_score).
"""

import os
import pandas as pd

VSA_PATH  = "data/stock_vsa.parquet"
FUND_PATH = "data/fundamentals.parquet"

CHANNEL_PTS = {
    "middle": 3,
    "lower": 3,
    "upper": 1,
    "unknown": 1,
    "breakdown": 0,   # a breakdown is broken structure, not a buy-the-dip
    "extended": 0,
}
STATE_PTS = {"up": 4, "inconclusive": 2, "down": 0}


def fundamental_pts(score):
    if pd.isna(score):
        return 0
    s = int(score)
    if s >= 5: return 2
    if s in (3, 4): return 1
    return 0


def main():
    df = pd.read_parquet(VSA_PATH)

    # --- fundamentals (static per ticker) ---
    if os.path.exists(FUND_PATH):
        fund = pd.read_parquet(FUND_PATH)[["ticker", "fundamental_score"]]
        df = df.merge(fund, on="ticker", how="left")
    else:
        df["fundamental_score"] = pd.NA

    # --- component scores ---
    # Channel: unknown for missing/blank zones (e.g. too few bars for regression)
    zone = df["channel_zone"].fillna("unknown").replace("", "unknown")
    df["conv_channel"] = zone.map(CHANNEL_PTS).fillna(1).astype(int)

    df["conv_fund"] = df["fundamental_score"].apply(fundamental_pts).astype(int)

    df["conv_state"] = df["wl_state"].map(STATE_PTS).fillna(0).astype(int)

    # Flip recency: any flip in the trailing 5-bar window (inclusive), per ticker
    df = df.sort_values(["ticker", "date"]).reset_index(drop=True)
    df["conv_flip"] = (
        df.groupby("ticker")["wl_flip"]
          .transform(lambda s: s.astype(int).rolling(5, min_periods=1).max())
          .astype(int)
    )

    df["conviction_score"] = (
        df["conv_channel"] + df["conv_fund"] + df["conv_state"] + df["conv_flip"]
    ).astype(int)

    # Persist only the final score — keep the parquet schema clean. The merged
    # fundamental_score and the per-component helper columns stay in memory for
    # the report below. (daily_signals / dashboard re-merge fundamentals.)
    helper_cols = ["fundamental_score", "conv_channel", "conv_fund",
                   "conv_state", "conv_flip"]
    df.drop(columns=helper_cols).to_parquet(VSA_PATH, engine="pyarrow", index=False)

    # --- report on the latest bar per ticker ---
    latest = df.sort_values("date").groupby("ticker").tail(1)
    print("Conviction score added to", VSA_PATH)
    print(f"\nLatest-bar distribution ({latest['ticker'].nunique()} tickers):")
    dist = latest["conviction_score"].value_counts().sort_index()
    for score, n in dist.items():
        bar = "█" * n
        print(f"  {int(score):>2}: {n:>3}  {bar}")

    top = (latest[latest["conviction_score"] >= 8]
           .sort_values("conviction_score", ascending=False))
    print(f"\nHighest conviction (>=8): {len(top)} tickers")
    if len(top):
        cols = ["ticker", "conviction_score", "conv_channel", "conv_fund",
                "conv_state", "conv_flip", "wl_state", "channel_zone"]
        print(top[cols].to_string(index=False))


if __name__ == "__main__":
    main()
