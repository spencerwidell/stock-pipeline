import pandas as pd
import numpy as np

PORTFOLIO = [
    "AMZN", "NVDA", "MSFT", "META", "TSLA",
    "ELF", "CELH", "PLTR", "AVGO", "SOFI",
    "TSM", "NOW", "IBM", "CRM", "ORCL",
]

print("Loading data...")
df = pd.read_parquet("data/stock_vsa.parquet")
df = df.sort_values(["ticker", "date"]).reset_index(drop=True)

# Compute gap from flip for each bar
df["gap_from_flip"] = ((df["close"] - df["flip_price"]) / df["flip_price"] * 100).round(2)

start_dates = {}
for ticker in PORTFOLIO:
    tdf = df[df["ticker"] == ticker]
    if len(tdf) > 0:
        start_dates[ticker] = tdf["date"].min()
common_start = max(start_dates.values())
common_end   = df["date"].max()
print(f"Common period: {common_start.date()} to {common_end.date()}")
print()

# Buy and hold baseline
bah_returns = {}
for ticker in PORTFOLIO:
    tdf = df[(df["ticker"] == ticker) & (df["date"] >= common_start)]
    if len(tdf) < 2:
        continue
    ret = (tdf.iloc[-1]["close"] / tdf.iloc[0]["close"] - 1) * 100
    bah_returns[ticker] = ret

def run_strategy(name, entry_fn, exit_fn):
    """Generic backtest engine."""
    results = {}
    for ticker in PORTFOLIO:
        tdf = df[(df["ticker"] == ticker) & (df["date"] >= common_start)].copy()
        if len(tdf) < 2:
            continue

        in_trade    = False
        entry_price = None
        total_ret   = 1.0
        wins        = 0
        trades      = 0
        days_in     = 0

        for _, row in tdf.iterrows():
            if not in_trade:
                if entry_fn(row):
                    in_trade    = True
                    entry_price = row["close"]
            else:
                days_in += 1
                if exit_fn(row):
                    trade_ret = row["close"] / entry_price
                    total_ret *= trade_ret
                    if trade_ret > 1:
                        wins += 1
                    trades    += 1
                    in_trade   = False
                    entry_price = None

        # Close any open trade at end
        if in_trade:
            last_close = tdf.iloc[-1]["close"]
            trade_ret  = last_close / entry_price
            total_ret *= trade_ret
            if trade_ret > 1:
                wins += 1
            trades += 1
            days_in += 1

        total_pct = (total_ret - 1) * 100
        win_rate  = wins / trades * 100 if trades > 0 else 0
        in_mkt    = days_in / len(tdf) * 100 if len(tdf) > 0 else 0
        results[ticker] = {
            "total_ret": total_pct,
            "trades":    trades,
            "win_rate":  win_rate,
            "in_market": in_mkt,
            "bah":       bah_returns.get(ticker, 0)
        }
    return results

def print_results(name, results):
    print(f"\n{'='*60}")
    print(f"STRATEGY: {name}")
    print(f"{'='*60}")
    for ticker, r in results.items():
        print(f"  {ticker:<6}: {r['trades']:>2} trades  "
              f"total_ret={r['total_ret']:>8.1f}%  "
              f"win={r['win_rate']:>4.0f}%  "
              f"bah={r['bah']:>8.1f}%")
    sys_avg = np.mean([r["total_ret"] for r in results.values()])
    bah_avg = np.mean([r["bah"] for r in results.values()])
    wins    = sum(1 for r in results.values() if r["total_ret"] > r["bah"])
    print(f"\nSystem avg:     {sys_avg:.1f}%")
    print(f"Buy-hold avg:   {bah_avg:.1f}%")
    print(f"System edge:    {sys_avg - bah_avg:+.1f}%")
    print(f"Beats BAH:      {wins}/{len(results)} names")
    return sys_avg, bah_avg

# V3 baseline rules
def v3_entry(row):
    return (row["wl_flip"] == True and
            row["wl_state"] == "up" and
            row["composite"] >= 2)

def v3_exit(row):
    return (row["wl_state"] == "down" and
            row["composite"] <= -3 and
            row["regime"] == "bear")

# V4a: gap filter — only enter when gap from flip < 2%
def v4a_entry(row):
    return (row["wl_flip"] == True and
            row["wl_state"] == "up" and
            row["composite"] >= 2 and
            pd.notna(row["gap_from_flip"]) and
            row["gap_from_flip"] < 2.0)

def v4a_exit(row):
    return v3_exit(row)

# V4b: gap filter tighter — entry only at flip day (gap = 0)
def v4b_entry(row):
    return (row["wl_flip"] == True and
            row["wl_state"] == "up" and
            row["composite"] >= 2 and
            pd.notna(row["gap_from_flip"]) and
            row["gap_from_flip"] < 5.0)

def v4b_exit(row):
    return v3_exit(row)

# V4c: validation filter — only enter after Day 2+ in up state
def v4c_entry(row):
    return (row["wl_state"] == "up" and
            row["composite"] >= 2 and
            pd.notna(row["wl_duration"]) and
            row["wl_duration"] == 2 and
            pd.notna(row["gap_from_flip"]) and
            row["gap_from_flip"] < 5.0)

def v4c_exit(row):
    return v3_exit(row)

# Run all strategies
r_v3  = run_strategy("V3 Baseline (flip+score≥2)", v3_entry, v3_exit)
r_v4a = run_strategy("V4a Gap Filter <2%",         v4a_entry, v4a_exit)
r_v4b = run_strategy("V4b Gap Filter <5%",         v4b_entry, v4b_exit)
r_v4c = run_strategy("V4c Day 2 Validation + gap<5%", v4c_entry, v4c_exit)

avg_v3,  bah = print_results("V3 Baseline (flip+score≥2)", r_v3)
avg_v4a, _   = print_results("V4a Gap Filter <2%",         r_v4a)
avg_v4b, _   = print_results("V4b Gap Filter <5%",         r_v4b)
avg_v4c, _   = print_results("V4c Day 2 Validation + gap<5%", r_v4c)

print(f"\n{'='*60}")
print("SUMMARY COMPARISON")
print(f"{'='*60}")
print(f"Buy and Hold:              {bah:.1f}%")
print(f"V3 Baseline:               {avg_v3:.1f}%  ({avg_v3-bah:+.1f}% vs BAH)")
print(f"V4a Gap <2%:               {avg_v4a:.1f}%  ({avg_v4a-bah:+.1f}% vs BAH)")
print(f"V4b Gap <5%:               {avg_v4b:.1f}%  ({avg_v4b-bah:+.1f}% vs BAH)")
print(f"V4c Day2 + gap<5%:         {avg_v4c:.1f}%  ({avg_v4c-bah:+.1f}% vs BAH)")

# ── Full universe backtest ─────────────────────────────────
print(f"\n{'='*60}")
print("FULL UNIVERSE — 88 TICKERS")
print(f"{'='*60}")

FULL_UNIVERSE = df["ticker"].unique().tolist()
# Remove META duplicate handling
FULL_UNIVERSE = [t for t in FULL_UNIVERSE if t != "FB"]

def run_strategy_universe(name, entry_fn, exit_fn, universe):
    results = {}
    for ticker in universe:
        tdf = df[df["ticker"] == ticker].copy()
        if len(tdf) < 60:  # skip tickers with less than 60 days history
            continue

        in_trade    = False
        entry_price = None
        total_ret   = 1.0
        wins        = 0
        trades      = 0

        for _, row in tdf.iterrows():
            if not in_trade:
                if entry_fn(row):
                    in_trade    = True
                    entry_price = row["close"]
            else:
                if exit_fn(row):
                    trade_ret  = row["close"] / entry_price
                    total_ret *= trade_ret
                    if trade_ret > 1:
                        wins += 1
                    trades   += 1
                    in_trade  = False

        if in_trade:
            trade_ret  = tdf.iloc[-1]["close"] / entry_price
            total_ret *= trade_ret
            if trade_ret > 1:
                wins += 1
            trades += 1

        # BAH for this ticker
        bah_ret = (tdf.iloc[-1]["close"] / tdf.iloc[0]["close"] - 1) * 100
        results[ticker] = {
            "total_ret": (total_ret - 1) * 100,
            "trades":    trades,
            "bah":       bah_ret
        }
    return results

def print_universe_summary(name, results):
    sys_avg = np.mean([r["total_ret"] for r in results.values()])
    bah_avg = np.mean([r["bah"] for r in results.values()])
    beats   = sum(1 for r in results.values() if r["total_ret"] > r["bah"])
    total   = len(results)
    print(f"\n{name}")
    print(f"  Tickers tested:  {total}")
    print(f"  System avg:      {sys_avg:.1f}%")
    print(f"  BAH avg:         {bah_avg:.1f}%")
    print(f"  Edge vs BAH:     {sys_avg - bah_avg:+.1f}%")
    print(f"  Beats BAH:       {beats}/{total} names")
    return sys_avg, bah_avg

ru_v3  = run_strategy_universe("V3",  v3_entry,  v3_exit,  FULL_UNIVERSE)
ru_v4a = run_strategy_universe("V4a", v4a_entry, v4a_exit, FULL_UNIVERSE)
ru_v4b = run_strategy_universe("V4b", v4b_entry, v4b_exit, FULL_UNIVERSE)
ru_v4c = run_strategy_universe("V4c", v4c_entry, v4c_exit, FULL_UNIVERSE)

print_universe_summary("V3  Baseline (flip+score≥2)",      ru_v3)
print_universe_summary("V4a Gap Filter <2%",                ru_v4a)
print_universe_summary("V4b Gap Filter <5%",                ru_v4b)
print_universe_summary("V4c Day2 Validation + gap<5%",      ru_v4c)
