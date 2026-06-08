import pandas as pd
import duckdb
from datetime import date

print(f"Widell Line Daily Signals — {date.today()}")
print("=" * 65)

df = duckdb.query("""
    WITH latest AS (
        SELECT ticker, date, close, wl_state, wl_flip,
               regime, composite, rsi_14, dist_52w_high,
               dist_ma200, vsa_label,
               ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY date DESC) as rn
        FROM 'data/stock_vsa.parquet'
    )
    SELECT ticker, date, ROUND(close, 2) as close,
           wl_state, wl_flip, regime, composite,
           ROUND(rsi_14, 1) as rsi,
           ROUND(dist_52w_high, 1) as dist_52w_hi,
           ROUND(dist_ma200, 1) as dist_ma200,
           vsa_label
    FROM latest
    WHERE rn = 1
    ORDER BY composite DESC, wl_state, ticker
""").df()

# State emoji
state_icon = {"up": "🟢", "inconclusive": "🟡", "down": "🔴"}
regime_icon = {"bull": "📈", "mixed": "↔️", "bear": "📉"}

print(f"\n{'Ticker':<6} {'Close':>7} {'State':<6} {'Regime':<6} "
      f"{'Score':>6} {'RSI':>5} {'52wH%':>6} {'MA200%':>7} {'VSA Label'}")
print("-" * 75)

for _, row in df.iterrows():
    icon  = state_icon.get(row["wl_state"], "?")
    ricon = regime_icon.get(row["regime"], "?")
    flip  = " ⚡" if row["wl_flip"] else ""
    print(f"{row['ticker']:<6} {row['close']:>7.2f} "
          f"{icon} {row['wl_state']:<13}"
          f"{ricon} {row['regime']:<8}"
          f"{row['composite']:>5} "
          f"{row['rsi']:>5.1f} "
          f"{row['dist_52w_hi']:>6.1f}% "
          f"{row['dist_ma200']:>6.1f}% "
          f"  {row['vsa_label']}{flip}")

print()
print("Legend: 🟢 up  🟡 inconclusive  🔴 down  ⚡ flip today")
print(f"        📈 bull  ↔️  mixed  📉 bear")
print()

# Summary
up   = (df["wl_state"] == "up").sum()
down = (df["wl_state"] == "down").sum()
inc  = (df["wl_state"] == "inconclusive").sum()
flips = df["wl_flip"].sum()

print(f"Universe: {up} up  {inc} inconclusive  {down} down  |  {flips} flip(s) today")
print(f"High score (>=2): {(df['composite'] >= 2).sum()} tickers")
print(f"Low score (<=-3): {(df['composite'] <= -3).sum()} tickers")
