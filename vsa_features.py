import pandas as pd
import pyarrow.parquet as pq

# Load base data
df = pd.read_parquet("data/stock_ohlcv.parquet")

# Sort so rolling calculations work correctly
df = df.sort_values(["ticker", "date"]).reset_index(drop=True)

# Bar direction
df["direction"] = (df["close"] > df["open"]).map({True: "up", False: "down"})

# Spread (range of the bar)
df["spread"] = df["high"] - df["low"]

# Volume relative to 10-day rolling average, per ticker
df["vol_ma10"] = df.groupby("ticker")["volume"].transform(
    lambda x: x.rolling(10, min_periods=1).mean()
)
df["rel_volume"] = (df["volume"] / df["vol_ma10"]).round(2)

# Save
df.to_parquet("data/stock_vsa.parquet", engine="pyarrow", index=False)
print(f"Saved {len(df)} rows to data/stock_vsa.parquet")
print(df[["ticker", "date", "direction", "spread", "rel_volume"]].head(10).to_string(index=False))
