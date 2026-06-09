import pandas as pd
import numpy as np
from sector_map import SECTOR_MAP

print("Loading data...")
df = pd.read_parquet("data/stock_vsa.parquet")
df = df.sort_values(["ticker", "date"]).reset_index(drop=True)

# Build a lookup: date -> ticker -> wl_state and composite
pivot_state = df.pivot(index="date", columns="ticker", values="wl_state")
pivot_comp  = df.pivot(index="date", columns="ticker", values="composite")
pivot_close = df.pivot(index="date", columns="ticker", values="close")
pivot_flip  = df.pivot(index="date", columns="ticker", values="wl_flip")

# Backtest parameters
ENTRY_MIN_COMPOSITE  =  2
HOLD_MIN_COMPOSITE   =  0
EXIT_MAX_COMPOSITE   = -2
TRANSACTION_COST     =  0.001  # 0.1% per trade (entry + exit)
INITIAL_CAPITAL      =  100000

# Only backtest individual stocks (not ETFs)
STOCK_TICKERS = [t for t in SECTOR_MAP.keys()]

dates = sorted(df["date"].unique())
results = []

for ticker in STOCK_TICKERS:
    if ticker not in pivot_state.columns:
        continue

    sector_etf = SECTOR_MAP[ticker]["sector_etf"]
    broad_etf  = SECTOR_MAP[ticker]["broad_etf"]

    in_position = False
    entry_price = None
    entry_date  = None
    trades = []

    for i, date in enumerate(dates):
        if ticker not in pivot_state.columns:
            continue

        try:
            state     = pivot_state.loc[date, ticker]
            comp      = pivot_comp.loc[date, ticker]
            price     = pivot_close.loc[date, ticker]
            flip      = pivot_flip.loc[date, ticker]
            spy_state = pivot_state.loc[date, "SPY"] if "SPY" in pivot_state.columns else "inconclusive"
            sec_state = pivot_state.loc[date, sector_etf] if sector_etf in pivot_state.columns else "inconclusive"
        except:
            continue

        if pd.isna(price) or pd.isna(state) or pd.isna(comp):
            continue

        if not in_position:
            # Entry conditions
            entry_ok = (
                flip == True and
                state == "up" and
                comp >= ENTRY_MIN_COMPOSITE and
                spy_state != "down" and
                sec_state != "down"
            )
            if entry_ok:
                in_position = True
                entry_price = price * (1 + TRANSACTION_COST)
                entry_date  = date

        else:
            # Exit conditions
            exit_ok = (
                state == "down" or
                comp <= EXIT_MAX_COMPOSITE
            )
            if exit_ok or i == len(dates) - 1:
                exit_price = price * (1 - TRANSACTION_COST)
                ret = (exit_price - entry_price) / entry_price * 100
                days_held = (date - entry_date).days
                trades.append({
                    "ticker":      ticker,
                    "entry_date":  entry_date,
                    "exit_date":   date,
                    "entry_price": round(entry_price, 2),
                    "exit_price":  round(exit_price, 2),
                    "return_pct":  round(ret, 2),
                    "days_held":   days_held,
                })
                in_position = False
                entry_price = None
                entry_date  = None

    results.extend(trades)

# Results
trades_df = pd.DataFrame(results)

if len(trades_df) == 0:
    print("No trades generated.")
else:
    print(f"\nBacktest Results — Widell Line Swing Strategy")
    print(f"Entry: flip to up + composite >= {ENTRY_MIN_COMPOSITE} + SPY/sector not down")
    print(f"Exit:  state = down OR composite <= {EXIT_MAX_COMPOSITE}")
    print(f"Transaction cost: {TRANSACTION_COST*100:.1f}% per side")
    print("=" * 55)
    print(f"Total trades:      {len(trades_df)}")
    print(f"Win rate:          {(trades_df['return_pct'] > 0).mean()*100:.1f}%")
    print(f"Avg return/trade:  {trades_df['return_pct'].mean():.2f}%")
    print(f"Median return:     {trades_df['return_pct'].median():.2f}%")
    print(f"Avg days held:     {trades_df['days_held'].mean():.1f}")
    print(f"Best trade:        {trades_df['return_pct'].max():.2f}%")
    print(f"Worst trade:       {trades_df['return_pct'].min():.2f}%")
    print(f"Std dev:           {trades_df['return_pct'].std():.2f}%")

    print(f"\nResults by ticker:")
    by_ticker = trades_df.groupby("ticker").agg(
        trades=("return_pct", "count"),
        avg_return=("return_pct", "mean"),
        win_rate=("return_pct", lambda x: (x > 0).mean() * 100)
    ).round(2).sort_values("avg_return", ascending=False)
    print(by_ticker.to_string())

    # SPY benchmark
    spy_prices = pivot_close["SPY"].dropna()
    spy_return = (spy_prices.iloc[-1] / spy_prices.iloc[0] - 1) * 100
    print(f"\nSPY buy-and-hold over same period: {spy_return:.1f}%")

    # Save trades
    trades_df.to_csv("data/backtest_trades.csv", index=False)
    print(f"\nTrades saved to data/backtest_trades.csv")
