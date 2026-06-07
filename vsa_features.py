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
df["roc_20"] = (df.groupby("ticker")["close"].transform(
    lambda x: (x - x.shift(20)) / x.shift(20) * 100
)).round(2)

# 52-week high and low distance
df["high_52w"] = df.groupby("ticker")["high"].transform(
    lambda x: x.rolling(252, min_periods=1).max()
)
df["low_52w"] = df.groupby("ticker")["low"].transform(
    lambda x: x.rolling(252, min_periods=1).min()
)
df["dist_52w_high"] = ((df["close"] - df["high_52w"]) /
                        df["high_52w"] * 100).round(2)
df["dist_52w_low"]  = ((df["close"] - df["low_52w"]) /
                        df["low_52w"] * 100).round(2)

# RSI (14-day)
def compute_rsi(series, period=14):
    delta    = series.diff()
    gain     = delta.clip(lower=0)
    loss     = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=period-1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period-1, min_periods=period).mean()
    rs = avg_gain / avg_loss
    return (100 - 100 / (1 + rs)).round(2)

df["rsi_14"] = df.groupby("ticker")["close"].transform(compute_rsi)

# MACD
def compute_macd_line(series):
    ema12 = series.ewm(span=12, min_periods=1).mean()
    ema26 = series.ewm(span=26, min_periods=1).mean()
    return (ema12 - ema26).round(3)

def compute_macd_signal(series):
    ema12  = series.ewm(span=12, min_periods=1).mean()
    ema26  = series.ewm(span=26, min_periods=1).mean()
    macd   = ema12 - ema26
    return macd.ewm(span=9, min_periods=1).mean().round(3)

df["macd"]        = df.groupby("ticker")["close"].transform(compute_macd_line)
df["macd_signal"] = df.groupby("ticker")["close"].transform(compute_macd_signal)
df["macd_hist"]   = (df["macd"] - df["macd_signal"]).round(3)

# MACD crossover — macd crosses above signal line
df["macd_prev"] = df.groupby("ticker")["macd"].transform(lambda x: x.shift(1))
df["sig_prev"] = df.groupby("ticker")["macd_signal"].transform(lambda x: x.shift(1))
df["macd_cross"] = ((df["macd"] > df["macd_signal"]) & (df["macd_prev"] < df["sig_prev"])).astype(int)

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

# Distance from 200MA as percentage
df["dist_ma200"] = ((df["close"] - df["ma200"]) / df["ma200"] * 100).round(2)

# Slope of 200MA
df["ma200_slope"] = df.groupby("ticker")["ma200"].transform(
    lambda x: x.diff(10) / x.shift(10) * 100
).round(3)

# MA stack regime
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
print(df[["ticker", "date", "close_pos", "rsi_14", "macd",
          "dist_52w_high", "roc_20"]].head(10).to_string(index=False))
