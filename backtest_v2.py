import pandas as pd
import numpy as np
from sector_map import SECTOR_MAP

print("Loading data...")
df = pd.read_parquet("data/stock_vsa.parquet")
df = df.sort_values(["ticker", "date"]).reset_index(drop=True)

pivot_state  = df.pivot(index="date", columns="ticker", values="wl_state")
pivot_comp   = df.pivot(index="date", columns="ticker", values="composite")
pivot_close  = df.pivot(index="date", columns="ticker", values="close")
pivot_flip   = df.pivot(index="date", columns="ticker", values="wl_flip")
pivot_regime = df.pivot(index="date", columns="ticker", values="regime")

# Philosophy-aligned parameters
ENTRY_MIN_COMPOSITE  =  2      # only enter on strong signal
STOP_COMPOSITE       = -3      # structural breakdown
STOP_STATE           = "down"  # price below support
TRANSACTION_COST     =  0.001  # 0.1% per side

STOCK_TICKERS = list(SECTOR_MAP.keys())
dates = sorted(df["date"].unique())

results = []

for ticker in STOCK_TICKERS:
    if ticker not in pivot_state.columns:
        continue

    sector_etf = SECTOR_MAP[ticker]["sector_etf"]
    broad_etf  = SECTOR_MAP[ticker]["broad_etf"]

    in_position  = False
    entry_price  = None
    entry_date   = None
    peak_price   = None

    for i, date in enumerate(dates):
        try:
            state      = pivot_state.loc[date, ticker]
            comp       = pivot_comp.loc[date, ticker]
            price      = pivot_close.loc[date, ticker]
            flip       = pivot_flip.loc[date, ticker]
            regime     = pivot_regime.loc[date, ticker]
            spy_state  = pivot_state.loc[date, "SPY"] if "SPY" in pivot_state.columns else "inconclusive"
            spy_regime = pivot_regime.loc[date, "SPY"] if "SPY" in pivot_regime.columns else "mixed"
            sec_state  = pivot_state.loc[date, sector_etf] if sector_etf in pivot_state.columns else "inconclusive"
        except:
            continue

        if pd.isna(price) or pd.isna(state) or pd.isna(comp):
            continue

        if not in_position:
            # Entry: flip to up, strong composite, top-down aligned
            entry_ok = (
                flip == True and
                state == "up" and
                comp >= ENTRY_MIN_COMPOSITE and
                spy_state != "down" and
                spy_regime != "bear" and
                sec_state != "down"
            )
            if entry_ok:
                in_position = True
                entry_price = price * (1 + TRANSACTION_COST)
                entry_date  = date
                peak_price  = price

        else:
            # Track peak for drawdown awareness
            if price > peak_price:
                peak_price = price

            # Exit only on structural breakdown
            structural_breakdown = (
                state == "down" and
                comp <= STOP_COMPOSITE and
                regime == "bear"
            )

            # Or catastrophic drawdown from peak (>35% from peak)
            drawdown_from_peak = (price - peak_price) / peak_price * 100
            catastrophic = drawdown_from_peak < -35

            if structural_breakdown or catastrophic or i == len(dates) - 1:
                exit_price = price * (1 - TRANSACTION_COST)
                ret = (exit_price - entry_price) / entry_price * 100
                days_held = (date - entry_date).days
                exit_reason = "structural" if structural_breakdown else \
                              "drawdown_stop" if catastrophic else "end_of_data"
                results.append({
                    "ticker":       ticker,
                    "entry_date":   entry_date,
                    "exit_date":    date,
                    "entry_price":  round(entry_price, 2),
                    "exit_price":   round(exit_price, 2),
                    "peak_price":   round(peak_price, 2),
                    "return_pct":   round(ret, 2),
                    "days_held":    days_held,
                    "exit_reason":  exit_reason,
                    "drawdown_pct": round(drawdown_from_peak, 1),
                })
                in_position = False
                entry_price = None
                entry_date  = None
                peak_price  = None

trades_df = pd.DataFrame(results)

if len(trades_df) == 0:
    print("No trades generated.")
else:
    print(f"\nBacktest V2 — Widell Line Trend Following")
    print(f"Entry: flip to up + composite >= {ENTRY_MIN_COMPOSITE} + top-down aligned")
    print(f"Exit:  structural breakdown (down + composite <= {STOP_COMPOSITE} + bear)")
    print(f"       OR >35% drawdown from peak")
    print(f"Transaction cost: {TRANSACTION_COST*100:.1f}% per side")
    print("=" * 60)
    print(f"Total trades:       {len(trades_df)}")
    print(f"Win rate:           {(trades_df['return_pct'] > 0).mean()*100:.1f}%")
    print(f"Avg return/trade:   {trades_df['return_pct'].mean():.2f}%")
    print(f"Median return:      {trades_df['return_pct'].median():.2f}%")
    print(f"Avg days held:      {trades_df['days_held'].mean():.1f}")
    print(f"Best trade:         {trades_df['return_pct'].max():.2f}%")
    print(f"Worst trade:        {trades_df['return_pct'].min():.2f}%")

    print(f"\nExit reasons:")
    print(trades_df['exit_reason'].value_counts().to_string())

    print(f"\nResults by ticker:")
    by_ticker = trades_df.groupby("ticker").agg(
        trades=("return_pct", "count"),
        avg_return=("return_pct", "mean"),
        win_rate=("return_pct", lambda x: (x > 0).mean() * 100),
        avg_days=("days_held", "mean")
    ).round(1).sort_values("avg_return", ascending=False)
    print(by_ticker.to_string())

    # SPY benchmark
    spy_prices = pivot_close["SPY"].dropna()
    spy_return = (spy_prices.iloc[-1] / spy_prices.iloc[0] - 1) * 100
    print(f"\nSPY buy-and-hold: {spy_return:.1f}%")

    trades_df.to_csv("data/backtest_v2_trades.csv", index=False)
    print(f"Trades saved to data/backtest_v2_trades.csv")
