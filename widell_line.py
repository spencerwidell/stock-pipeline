import pandas as pd
import numpy as np

# Load VSA features
df = pd.read_parquet("data/stock_vsa.parquet")
df = df.sort_values(["ticker", "date"]).reset_index(drop=True)

N = 3  # bars each side for swing detection

def add_widell(group):
    h = group["high"].values
    l = group["low"].values
    c = group["close"].values
    n = len(group)

    # Detect swing highs and lows
    swing_high = np.zeros(n, dtype=bool)
    swing_low  = np.zeros(n, dtype=bool)

    for i in range(N, n - N):
        window_h = h[i-N:i+N+1]
        window_l = l[i-N:i+N+1]
        if h[i] == window_h.max():
            swing_high[i] = True
        if l[i] == window_l.min():
            swing_low[i] = True

    # Forward-fill swing high/low to get current resistance/support
    resistance = np.full(n, np.nan)
    support    = np.full(n, np.nan)

    last_res = np.nan
    last_sup = np.nan
    for i in range(n):
        if swing_high[i]:
            last_res = h[i]
        if swing_low[i]:
            last_sup = l[i]
        resistance[i] = last_res
        support[i]    = last_sup

    # Assign state
    states = []
    for i in range(n):
        if np.isnan(resistance[i]) or np.isnan(support[i]):
            states.append("inconclusive")
        elif c[i] > resistance[i]:
            states.append("up")
        elif c[i] < support[i]:
            states.append("down")
        else:
            states.append("inconclusive")

    group = group.copy()
    group["swing_high"] = swing_high
    group["swing_low"]  = swing_low
    group["resistance"] = resistance
    group["support"]    = support
    group["wl_state"]   = states

    # Detect flips
    group["wl_flip"] = group["wl_state"] != group["wl_state"].shift(1)
    # Price at the flip — forward filled so every bar knows the last flip price
    group["flip_price"] = group["close"].where(group["wl_flip"])
    group["flip_price"] = group["flip_price"].ffill()
    group["flip_date"] = group["date"].where(group["wl_flip"])
    group["flip_date"] = group["flip_date"].ffill()
    return group

df = df.groupby("ticker", group_keys=False).apply(add_widell)
if "ticker" not in df.columns:
    df.insert(0, "ticker", df.index.get_level_values("ticker"))

# Save
df.to_parquet("data/stock_vsa.parquet", engine="pyarrow", index=False)

# Summary
print(df["wl_state"].value_counts().to_string())
print()
print(df["wl_flip"].value_counts().to_string())
