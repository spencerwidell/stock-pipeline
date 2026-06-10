import os
import requests
import pandas as pd
import duckdb
from datetime import date

def load_env():
    with open(".env") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            k, v = line.split("=", 1)
            os.environ[k] = v

load_env()
TOKEN   = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})

# Load signals
df = duckdb.query("""
    WITH latest AS (
        SELECT ticker, date, close, wl_state, wl_flip,
               regime, composite, conviction_score, rsi_14, flip_price, resistance,
               CASE
                   WHEN wl_state = 'up' THEN 'pullback'
                   WHEN wl_state = 'inconclusive' THEN 'breakout'
                   ELSE 'resistance'
               END as level_type,
               ROUND((close - flip_price) / flip_price * 100, 1) as gap_from_flip,
               wl_duration,
               ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY date DESC) as rn
        FROM 'data/stock_vsa.parquet'
    )
    SELECT * FROM latest WHERE rn = 1
""").df()

today = date.today().strftime("%Y-%m-%d")

# Join fundamentals
import os
if os.path.exists("data/fundamentals.parquet"):
    fund_df = pd.read_parquet("data/fundamentals.parquet")[
        ["ticker","fundamental_score"]
    ]
    df = df.merge(fund_df, on="ticker", how="left")
else:
    df["fundamental_score"] = None

# Build message
lines = [f"📈 *Widell Line Signals — {today}*\n"]

# Summary
up   = (df["wl_state"] == "up").sum()
inc  = (df["wl_state"] == "inconclusive").sum()
down = (df["wl_state"] == "down").sum()
flips = df["wl_flip"].sum()
lines.append(f"Universe: {up} 🟢  {inc} 🟡  {down} 🔴  |  {int(flips)} flip(s)\n")

# Flips today
flipped = df[df["wl_flip"] == True]
if len(flipped) > 0:
    lines.append("*⚡ Flips Today:*")
    for _, row in flipped.iterrows():
        icon = "🟢" if row["wl_state"] == "up" else \
               "🔴" if row["wl_state"] == "down" else "🟡"
        gap  = f"{row['gap_from_flip']:+.1f}%" if pd.notna(row["gap_from_flip"]) else ""
        lines.append(f"{icon} *{row['ticker']}* {row['wl_state'].upper()} "
                     f"score={int(row['composite'])} {gap}")
else:
    lines.append("No flips today.")

lines.append("")

# Up state with gap analysis
up_df = df[df["wl_state"] == "up"].sort_values("composite", ascending=False)
if len(up_df) > 0:
    lines.append("*🟢 Up State:*")
    for _, row in up_df.iterrows():
        gap  = f"{row['gap_from_flip']:+.1f}%" if pd.notna(row["gap_from_flip"]) else ""
        pb   = f"{row['level_type']}→${row['resistance']:.2f}" if pd.notna(row["resistance"]) else ""
        chase = "🔴chase" if pd.notna(row["gap_from_flip"]) and row["gap_from_flip"] > 5 else \
                "🟡elev" if pd.notna(row["gap_from_flip"]) and row["gap_from_flip"] > 2 else \
                "🟢entry"
        days = int(row["wl_duration"]) if pd.notna(row["wl_duration"]) else 0
        fund = f"F:{int(row['fundamental_score'])}/5" if pd.notna(row.get('fundamental_score')) else "F:N/A"
        conv = f"conv:{int(row['conviction_score'])}/10" if pd.notna(row.get('conviction_score')) else ""
        lines.append(f"  *{row['ticker']}* ${row['close']:.2f} "
                     f"{chase} {gap} {pb} {fund} {conv} d={days}")

lines.append("")

# High score opportunities
high = df[(df["composite"] >= 2) & (df["wl_state"] != "up")]
if len(high) > 0:
    lines.append("*🔥 High Score (≥2, not yet up):*")
    for _, row in high.iterrows():
        lines.append(f"  *{row['ticker']}* score={int(row['composite'])} "
                     f"{row['wl_state']} {row['regime']}")

lines.append("")
lines.append(f"Dashboard: http://18.188.180.99:8501")

msg = "\n".join(lines)
send(msg)
print("Alert sent.")
print(msg)
