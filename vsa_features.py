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

# Spread relative to 10-day rolling average, per ticker
df["spread_ma10"] = df.groupby("ticker")["spread"].transform(
    lambda x: x.rolling(10, min_periods=1).mean()
)
df["rel_spread"] = (df["spread"] / df["spread_ma10"]).round(2)


# Volume relative to 10-day rolling average, per ticker
df["vol_ma10"] = df.groupby("ticker")["volume"].transform(
    lambda x: x.rolling(10, min_periods=1).mean()
)

df["rel_volume"] = (df["volume"] / df["vol_ma10"]).round(2)

# Close position within bar (0=closed at low, 1=closed at high)
df["close_pos"] = ((df["close"] - df["low"]) /
                   (df["high"] - df["low"])).round(3)

# Upper and lower wick ratios
bar_range = df["high"] - df["low"]
df["upper_wick"] = ((df["high"] - df[["open","close"]].max(axis=1)) /
                    bar_range).round(3)
df["lower_wick"] = ((df[["open","close"]].min(axis=1) - df["low"]) /
                    bar_range).round(3)

# Effort — spread * volume normalized
df["effort"] = (df["rel_spread"] * df["rel_volume"]).round(3)

# Rate of change — 20 day momentum
df["roc_20"] = ((df["close"] - df.groupby("ticker")["close"].transform(
    lambda x: x.shift(20))) /
    df.groupby("ticker")["close"].transform(
    lambda x: x.shift(20)) * 100).round(2)

# Distance from 52-week high and low
df["high_52w"] = df.groupby("ticker")["high"].transform(
    lambda x: x.rolling(252, min_periods=1).max()
)
df["low_52w"] = df.groupby("ticker")["low"].transform(
    lambda x: x.rolling(252, min_periods=1).min()
)
df["dist_52w_high"] = ((df["close"] - df["high_52w"]) /
                        df["high_52w"] * 100).round(2)
df["dist_52w_low"] = ((df["close"] - df["low_52w"]) /
                       df["low_52w"] * 100).round(2)



# 200-day MA and regime
df["ma200"] = df.groupby("ticker")["close"].transform(
    lambda x: x.rolling(200, min_periods=1).mean()
)
df["ma50"] = df.groupby("ticker")["close"].transform(
    lambda x: x.rolling(50, min_periods=1).mean()
)
df["ma20"] = df.groupby("ticker")["close"].transform(
    lambda x: x.rolling(20, min_periods=1).mean()
)

# Distance from 200MA as percentage — positive = above, negative = below
df["dist_ma200"] = ((df["close"] - df["ma200"]) / df["ma200"] * 100).round(2)

# Slope of 200MA — is it rising or falling?
df["ma200_slope"] = df.groupby("ticker")["ma200"].transform(
    lambda x: x.diff(10) / x.shift(10) * 100
).round(3)

# MA stack regime — bull when 20 > 50 > 200, bear when 20 < 50 < 200
def ma_regime(row):
    if row["ma20"] > row["ma50"] > row["ma200"]:
        return "bull"
    elif row["ma20"] < row["ma50"] < row["ma200"]:
        return "bear"
    else:
        return "mixed"

df["regime"] = df.apply(ma_regime, axis=1)

# Channel position — standard deviation bands around MA20
df["ma20_std"] = df.groupby("ticker")["close"].transform(
    lambda x: x.rolling(20, min_periods=1).std()
)
df["channel_pos"] = ((df["close"] - df["ma20"]) / df["ma20_std"]).round(2)

# Save
df.to_parquet("data/stock_vsa.parquet", engine="pyarrow", index=False)
print(f"Saved {len(df)} rows to data/stock_vsa.parquet")
print(df[["ticker", "date", "close_pos", "upper_wick", "lower_wick",
          "effort", "roc_20", "dist_52w_high"]].head(10).to_string(index=False))
