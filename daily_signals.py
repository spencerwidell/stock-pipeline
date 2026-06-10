import pandas as pd
import duckdb
from datetime import date

print(f"Widell Line Daily Signals — {date.today()}")
print("=" * 95)

df = duckdb.query("""
    WITH latest AS (
        SELECT ticker, date, close, wl_state, wl_flip,
               regime, composite, conviction_score, rsi_14, dist_52w_high,
               dist_ma200, ma200, ma50, ma20,
               vsa_label, wl_duration,
               flip_price, resistance, channel_pos, channel_zone,
               ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY date DESC) as rn
        FROM 'data/stock_vsa.parquet'
    )
    SELECT ticker, date, ROUND(close,2) as close,
           wl_state, wl_flip, regime, composite, conviction_score,
           ROUND(rsi_14,1) as rsi,
           ROUND(dist_52w_high,1) as dist_52w_hi,
           ROUND(dist_ma200,1) as dist_ma200,
           ROUND(ma200,2) as ma200,
           ROUND(ma50,2) as ma50,
           CAST(wl_duration AS INT) as days,
           ROUND(channel_pos, 3) as channel_pos,
           channel_zone,
           vsa_label,
           ROUND(flip_price,2) as flip_price,
           ROUND(resistance,2) as key_level,
           CASE
               WHEN wl_state = 'up' THEN 'pullback'
               WHEN wl_state = 'inconclusive' THEN 'breakout'
               ELSE 'resistance'
           END as level_type,
           ROUND((close - flip_price) / flip_price * 100, 1) as gap_from_flip
    FROM latest
    WHERE rn = 1
    ORDER BY composite DESC, wl_state, ticker
""").df()

# Join fundamentals
import os
if os.path.exists("data/fundamentals.parquet"):
    fund_df = pd.read_parquet("data/fundamentals.parquet")[
        ["ticker","fundamental_score","rev_growth_yoy","gross_margin"]
    ]
    df = df.merge(fund_df, on="ticker", how="left")
else:
    df["fundamental_score"] = None
    df["rev_growth_yoy"]    = None
    df["gross_margin"]      = None


state_icon  = {"up": "🟢", "inconclusive": "🟡", "down": "🔴"}
regime_icon = {"bull": "📈", "mixed": "↔️",  "bear": "📉"}

print(f"\n{'Ticker':<6} {'Close':>7} {'State':<6} {'Regime':<6} "
      f"{'Scr':>4} {'Conv':>5} {'RSI':>5} {'52wH%':>6} {'MA200%':>7} "
      f"{'MA200':>8} {'MA50':>8} {'Days':>5} {'VSA Label'}")
print("-" * 95)

for _, row in df.iterrows():
    icon  = state_icon.get(row["wl_state"], "?")
    ricon = regime_icon.get(row["regime"], "?")
    flip  = " ⚡" if row["wl_flip"] else ""
    days  = int(row["days"]) if pd.notna(row["days"]) else 0
    print(f"{row['ticker']:<6} {row['close']:>7.2f} "
          f"{icon} {row['wl_state']:<13}"
          f"{ricon} {row['regime']:<8}"
          f"{row['composite']:>4} "
          f"{int(row['conviction_score']):>5} "
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

print(f"\nFlips today:")
flipped = df[df["wl_flip"] == True]
if len(flipped) > 0:
    for _, row in flipped.iterrows():
        icon  = state_icon.get(row["wl_state"], "?")
        ricon = regime_icon.get(row["regime"], "?")
        gap   = f"{row['gap_from_flip']:+.1f}%" if pd.notna(row["gap_from_flip"]) else "N/A"
        level = f"{row['level_type']}→{row['key_level']:.2f}" if pd.notna(row["key_level"]) else ""
        print(f"  {row['ticker']:<6} {icon} {row['wl_state']:<13} "
              f"{ricon} {row['regime']:<8} score={row['composite']:>3}  "
              f"rsi={row['rsi']:>5.1f}  gap={gap}  {level}  {row['vsa_label']}")
else:
    print("  None today")

print(f"\nUp state — entry analysis:")
up_df = df[df["wl_state"] == "up"].copy()
if len(up_df) > 0:
    for _, row in up_df.iterrows():
        gap   = f"{row['gap_from_flip']:+.1f}%" if pd.notna(row["gap_from_flip"]) else "N/A"
        level = f"pullback→{row['key_level']:.2f}" if pd.notna(row["key_level"]) else ""
        days  = int(row["days"]) if pd.notna(row["days"]) else 0
        zone  = row["channel_zone"] if pd.notna(row["channel_zone"]) else ""
        gap_v = row["gap_from_flip"] if pd.notna(row["gap_from_flip"]) else 0
        chase = "🔴 CHASING+EXT" if gap_v > 5 and zone == "extended" else \
                "🔴 CHASING"    if gap_v > 5 else \
                "🟡 ELEVATED"   if gap_v > 2 else \
                "🟢 AT ENTRY"
        zone_icon = "📈ext" if zone == "extended" else \
                    "📈up"  if zone == "upper" else \
                    "➡️mid" if zone == "middle" else \
                    "📉low" if zone == "lower" else \
                    "💥brk" if zone == "breakdown" else ""
        fund = f"F:{int(row.get('fundamental_score', 0)) if pd.notna(row.get('fundamental_score')) else 'N'}/5"
        conv = f"conv={int(row['conviction_score'])}/10"
        print(f"  {row['ticker']:<6} ${row['close']:>8.2f}  {chase}  gap={gap:>7}  {level}  {zone_icon}  {fund}  {conv}  days={days}")




print(f"\nInconclusive — breakout levels to watch:")
inc_df = df[(df["wl_state"] == "inconclusive") & (df["composite"] >= 1)].head(10)
if len(inc_df) > 0:
    for _, row in inc_df.iterrows():
        level = f"breakout→{row['key_level']:.2f}" if pd.notna(row["key_level"]) else ""
        support = f"support→{row['close']:.2f}"
        pct_to_breakout = ((row["key_level"] - row["close"]) / row["close"] * 100) if pd.notna(row["key_level"]) else 0
        print(f"  {row['ticker']:<6} ${row['close']:>8.2f}  {level}  "
              f"({pct_to_breakout:+.1f}% away)  score={row['composite']}")
