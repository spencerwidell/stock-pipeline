import pandas as pd
import numpy as np

# Your 15 core names
PORTFOLIO = [
    "AMZN", "NVDA", "MSFT", "META", "TSLA",
    "ELF", "CELH", "PLTR", "AVGO", "SOFI",
    "TSM", "NOW", "IBM", "CRM", "ORCL",
]

print("Loading data...")
df = pd.read_parquet("data/stock_vsa.parquet")
df = df.sort_values(["ticker", "date"]).reset_index(drop=True)

# Find common start date across all 15 names
start_dates = {}
for ticker in PORTFOLIO:
    tdf = df[df["ticker"] == ticker]
    if len(tdf) > 0:
        start_dates[ticker] = tdf["date"].min()

common_start = max(start_dates.values())
common_end   = df["date"].max()

print(f"Common period: {common_start.date()} to {common_end.date()}")
print()

# Strategy 1: Buy and hold equally weighted from common_start
print("=" * 60)
print("STRATEGY 1: Buy and Hold (equal weight, all 15 names)")
print("=" * 60)

bah_returns = {}
for ticker in PORTFOLIO:
    tdf = df[(df["ticker"] == ticker) & (df["date"] >= common_start)]
    if len(tdf) < 2:
        continue
    start_price = tdf.iloc[0]["close"]
    end_price   = tdf.iloc[-1]["close"]
    ret = (end_price / start_price - 1) * 100
    bah_returns[ticker] = ret
    print(f"  {ticker:<6}: {ret:>8.1f}%")

portfolio_bah = np.mean(list(bah_returns.values()))
print(f"\nPortfolio avg return (equal weight): {portfolio_bah:.1f}%")

# Strategy 2: Widell Line timing within same names
print()
print("=" * 60)
print("STRATEGY 2: Widell Line Timing (same 15 names)")
print("=" * 60)
print("Entry: flip to up + composite >= 2")
print("Hold:  while state != down or composite > -3")
print("Exit:  state = down AND composite <= -3 AND regime = bear")
print()

pivot_state  = df.pivot(index="date", columns="ticker", values="wl_state")
pivot_comp   = df.pivot(index="date", columns="ticker", values="composite")
pivot_close  = df.pivot(index="date", columns="ticker", values="close")
pivot_flip   = df.pivot(index="date", columns="ticker", values="wl_flip")
pivot_regime = df.pivot(index="date", columns="ticker", values="regime")

TRANSACTION_COST = 0.001
dates = sorted(df[df["date"] >= common_start]["date"].unique())

all_trades = []

for ticker in PORTFOLIO:
    if ticker not in pivot_state.columns:
        continue

    in_position = False
    entry_price = None
    entry_date  = None
    peak_price  = None
    trades = []

    for i, date in enumerate(dates):
        try:
            state  = pivot_state.loc[date, ticker]
            comp   = pivot_comp.loc[date, ticker]
            price  = pivot_close.loc[date, ticker]
            flip   = pivot_flip.loc[date, ticker]
            regime = pivot_regime.loc[date, ticker]
        except:
            continue

        if pd.isna(price) or pd.isna(state) or pd.isna(comp):
            continue

        if not in_position:
            entry_ok = (
                flip == True and
                state == "up" and
                comp >= 2
            )
            if entry_ok:
                in_position = True
                entry_price = price * (1 + TRANSACTION_COST)
                entry_date  = date
                peak_price  = price
        else:
            if price > peak_price:
                peak_price = price

            drawdown = (price - peak_price) / peak_price * 100
            structural = (
                state == "down" and
                comp <= -3 and
                regime == "bear"
            )
            catastrophic = drawdown < -35

            if structural or catastrophic or i == len(dates) - 1:
                exit_price = price * (1 - TRANSACTION_COST)
                ret = (exit_price - entry_price) / entry_price * 100
                trades.append({
                    "ticker":      ticker,
                    "entry_date":  entry_date,
                    "exit_date":   date,
                    "return_pct":  round(ret, 2),
                    "days_held":   (date - entry_date).days,
                    "exit_reason": "structural" if structural else
                                   "drawdown" if catastrophic else "end",
                })
                in_position = False
                entry_price = None
                peak_price  = None

    # Time in market
    days_in_market = sum(t["days_held"] for t in trades)
    total_days = (dates[-1] - dates[0]).days
    pct_invested = days_in_market / total_days * 100 if total_days > 0 else 0

    if trades:
        ticker_return = sum(t["return_pct"] for t in trades)
        win_rate = sum(1 for t in trades if t["return_pct"] > 0) / len(trades) * 100
        print(f"  {ticker:<6}: {len(trades):>2} trades  "
              f"total_ret={ticker_return:>8.1f}%  "
              f"win={win_rate:>4.0f}%  "
              f"in_market={pct_invested:>4.0f}%  "
              f"bah={bah_returns.get(ticker,0):>8.1f}%")
        all_trades.extend(trades)
    else:
        print(f"  {ticker:<6}: no signals generated  "
              f"bah={bah_returns.get(ticker,0):>8.1f}%")

trades_df = pd.DataFrame(all_trades)
if len(trades_df) > 0:
    avg_system = trades_df.groupby("ticker")["return_pct"].sum().mean()
    print(f"\nSystem avg total return per ticker: {avg_system:.1f}%")
    print(f"Buy-and-hold avg:                   {portfolio_bah:.1f}%")
    print(f"\n% time in market (avg):             "
          f"{trades_df['days_held'].sum() / (len(PORTFOLIO) * len(dates)) * 100 * len(PORTFOLIO) / len(trades_df['ticker'].unique()):.0f}%")
