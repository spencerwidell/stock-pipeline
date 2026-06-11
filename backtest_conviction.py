"""Conviction backtest — does a higher conviction score actually lead to better
forward returns? Pressure-tested honestly; the report prints whatever the data says.

Method:
  - For every historical bar with a conviction_score, measure forward returns at
    5 / 20 / 60 trading days.
  - Report both RAW returns and SPY-RELATIVE alpha (strips market drift — the same
    target discipline used in the research phase).
  - Group by conviction bucket (0-3 / 4-5 / 6-7 / 8-10) and report count, mean,
    median, win rate, and SPY-relative mean.
  - Monotonicity: Spearman rank correlation between conviction and forward alpha
    (the real question — does MORE conviction mean MORE return, on average?).
  - Stress test by year (a headline that only works in one regime is not a result).
  - Primary test is SINGLE NAMES (the conviction buy thesis); ETFs reported separately.

HONEST CAVEAT (printed in the report too): conviction's fundamental sub-score (0-3 of
the 10) uses *current* fundamentals applied to past bars — a lookahead bias in that
component. The other 7 points (channel position, Widell state, flip recency) are
point-in-time and clean. So read the absolute edge with that caveat; the rank
ordering across buckets is the more trustworthy signal.

Usage:  python backtest_conviction.py
"""

import numpy as np
import pandas as pd

from sector_map import SECTOR_ETFS

VSA_PATH  = "data/stock_vsa.parquet"
HORIZONS  = [5, 20, 60]
NON_NAMES = set(SECTOR_ETFS) | {"SPY", "QQQ", "IWM", "GLD"}


def bucket(c):
    if pd.isna(c):
        return None
    if c >= 8:
        return "8-10 (high)"
    if c >= 6:
        return "6-7"
    if c >= 4:
        return "4-5"
    return "0-3 (low)"


def load():
    df = pd.read_parquet(VSA_PATH)[["ticker", "date", "close", "conviction_score"]]
    df = df.sort_values(["ticker", "date"]).reset_index(drop=True)
    # forward returns per ticker
    for n in HORIZONS:
        df[f"fwd_{n}"] = (df.groupby("ticker")["close"]
                         .transform(lambda s: s.shift(-n) / s - 1) * 100)
    # SPY-relative alpha: subtract SPY's forward return over the same window/date
    spy = df[df["ticker"] == "SPY"].set_index("date")
    for n in HORIZONS:
        df[f"alpha_{n}"] = df[f"fwd_{n}"] - df["date"].map(spy[f"fwd_{n}"])
    df["bucket"] = df["conviction_score"].apply(bucket)
    df["year"] = pd.to_datetime(df["date"]).dt.year
    return df


def report_table(df, label):
    print(f"\n{'='*78}\n{label}  (n={len(df):,} bars)\n{'='*78}")
    order = ["0-3 (low)", "4-5", "6-7", "8-10 (high)"]
    rows = []
    for b in order:
        g = df[df["bucket"] == b]
        if not len(g):
            continue
        rows.append({
            "bucket": b, "n": len(g),
            "raw_20d": g["fwd_20"].mean(),
            "alpha_5d": g["alpha_5"].mean(),
            "alpha_20d": g["alpha_20"].mean(),
            "alpha_60d": g["alpha_60"].mean(),
            "win%_20d": (g["fwd_20"] > 0).mean() * 100,
        })
    rep = pd.DataFrame(rows)
    if len(rep):
        print(rep.to_string(index=False, float_format=lambda x: f"{x:7.2f}"))
    # monotonicity — Spearman conviction vs forward alpha (the core question)
    sub = df.dropna(subset=["conviction_score", "alpha_20"])
    if len(sub) > 100:
        rho = sub["conviction_score"].corr(sub["alpha_20"], method="spearman")
        print(f"\nSpearman(conviction, 20d alpha): {rho:+.4f}  "
              f"({'higher conv → higher alpha' if rho > 0 else 'NO positive relationship'})")
    # high vs rest
    hi = df[df["conviction_score"] >= 8]["alpha_20"].mean()
    rest = df[df["conviction_score"] < 8]["alpha_20"].mean()
    if pd.notna(hi) and pd.notna(rest):
        print(f"Conv>=8 vs rest (20d alpha): {hi:+.2f}% vs {rest:+.2f}%  "
              f"-> edge {hi - rest:+.2f}%")
    return rep


def stress_by_year(df, label):
    print(f"\n--- Stress test: 20d alpha by conviction bucket x year ({label}) ---")
    piv = df.dropna(subset=["alpha_20", "bucket"]).pivot_table(
        index="bucket", columns="year", values="alpha_20", aggfunc="mean")
    order = [b for b in ["0-3 (low)", "4-5", "6-7", "8-10 (high)"] if b in piv.index]
    print(piv.loc[order].to_string(float_format=lambda x: f"{x:6.2f}"))


def main():
    df = load()
    print("CONVICTION BACKTEST — honest pressure test")
    print("CAVEAT: the fundamental sub-score (0-3 of 10) uses current fundamentals on")
    print("past bars (lookahead in that component); channel/state/flip (7 pts) are clean.")

    names = df[~df["ticker"].isin(NON_NAMES)]
    etfs  = df[df["ticker"].isin(NON_NAMES)]

    report_table(names, "SINGLE NAMES (the conviction buy thesis)")
    stress_by_year(names, "single names")
    report_table(etfs, "ETFs / broad (reference only — fundamentals N/A, conv_fund=0)")

    print("\n" + "=" * 78)
    print("Read: a real edge shows (1) alpha rising monotonically across buckets,")
    print("(2) positive Spearman, (3) a conv>=8 edge that holds across MOST years.")
    print("If it doesn't, the score needs rework — and that's a valid, useful result.")


if __name__ == "__main__":
    main()
