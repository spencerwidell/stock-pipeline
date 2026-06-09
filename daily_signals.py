import pandas as pd
import duckdb
from datetime import date

print(f"Widell Line Daily Signals — {date.today()}")
print("=" * 85)

df = duckdb.query("""
    WITH latest AS (
        SELECT ticker, date, close, wl_state, wl_flip,
               regime, composite, rsi_14, dist_52w_high,
               dist_ma200, ma200, ma50, ma20,
               vsa_label, wl_duration,
               ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY date DESC) as rn
        FROM 'data/stock_vsa.parquet'
    )
    SELECT ticker, date, ROUND(close, 2) as close,
           wl_state, wl_flip, regime, composite,
           ROUND(rsi_14, 1) as rsi,
           ROUND(dist_52w_high, 1) as dist_52w_hi,
           ROUND(dist_ma200, 1) as dist_ma200,
           ROUND(ma200, 2) as ma200,
           ROUND(ma50, 2) as ma50,
           wl_duration,
           vsa_label
    FROM latest
    WHERE rn = 1
    ORDER BY composite DESC, wl_state, ticker
""").df()

state_icon  = {"up": "🟢", "inconclusive": "🟡", "down": "🔴"}
regime_icon = {"bull": "📈", "mixed": "↔️",  "bear": "📉"}

print(f"\n{'Ticker':<6} {'Close':>7} {'State':<6} {'Regime':<6} "
      f"{'Scr':>4} {'RSI':>5} {'52wH%':>6} {'MA200%':>7} "
      f"{'MA200':>8} {'MA50':>8} {'Days':>5} {'VSA Label'}")
print("-" * 95)

for _, row in df.iterrows():
    icon  = state_icon.get(row["wl_state"], "?")
    ricon = regime_icon.get(row["regime"], "?")
    flip  = " ⚡" if row["wl_flip"] else ""
    days  = int(row["wl_duration"]) if pd.notna(row["wl_duration"]) else 0

    print(f"{row['ticker']:<6} {row['close']:>7.2f} "
          f"{icon} {row['wl_state']:<13}"
          f"{ricon} {row['regime']:<8}"
          f"{row['composite']:>4} "
          f"{row['rsi']:>5.1f} "
          f"{row['dist_52w_hi']:>6.1f}% "
          f"{row['dist_ma200']:>6.1f}% "
          f"{row['ma200']:>8.2f} "
          f"{row['ma50']:>8.2f} "
          f"{days:>5} "
          f"  {row['vsa_label']}{flip}")

print()
print("Legend: 🟢 up  🟡 inconclusive  🔴 down  ⚡ flip today  Days=consecutive days in state")
print(f"        📈 bull  ↔️  mixed  📉 bear")
print()

up    = (df["wl_state"] == "up").sum()
down  = (df["wl_state"] == "down").sum()
inc   = (df["wl_state"] == "inconclusive").sum()
flips = df["wl_flip"].sum()

print(f"Universe: {up} up  {inc} inconclusive  {down} down  |  {flips} flip(s) today")
print(f"High score (>=2): {(df['composite'] >= 2).sum()} tickers")
print(f"Low score (<=-3): {(df['composite'] <= -3).sum()} tickers")

# New flips today worth watching
print(f"\nFlips today:")
flipped = df[df["wl_flip"] == True][["ticker","wl_state","regime","composite","rsi","vsa_label"]]
if len(flipped) > 0:
    for _, row in flipped.iterrows():
        icon  = state_icon.get(row["wl_state"], "?")
        ricon = regime_icon.get(row["regime"], "?")
        print(f"  {row['ticker']:<6} {icon} {row['wl_state']:<13} "
              f"{ricon} {row['regime']:<8} score={row['composite']:>3}  "
              f"rsi={row['rsi']:>5.1f}  {row['vsa_label']}")
else:
    print("  None today")
