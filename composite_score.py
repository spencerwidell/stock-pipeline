import pandas as pd
import duckdb

# Load
df = pd.read_parquet("data/stock_vsa.parquet")

# Widell Line state score
wl_score = {"up": 2, "down": -2, "inconclusive": 0}
df["score_wl"] = df["wl_state"].map(wl_score)

# Flip score — direction depends on which state was flipped into
def flip_score(row):
    if not row["wl_flip"]:
        return 0
    if row["wl_state"] == "up":
        return 1
    if row["wl_state"] == "down":
        return -1
    return 0

df["score_flip"] = df.apply(flip_score, axis=1)

# VSA label score
vsa_score = {
    "buying_climax":  2,
    "effort_up":      1,
    "no_supply":      1,
    "neutral":        0,
    "no_demand":     -1,
    "effort_down":   -1,
    "selling_climax": -2,
}
df["score_vsa"] = df["vsa_label"].map(vsa_score)

# Regime score
regime_score = {"bull": 1, "mixed": 0, "bear": -1}
df["score_regime"] = df["regime"].map(regime_score)

# Composite
df["composite"] = (
    df["score_wl"] +
    df["score_flip"] +
    df["score_vsa"] +
    df["score_regime"]
)

# Sequence features — require full pipeline to be complete
df["rsi_trend"] = df.groupby("ticker")["rsi_14"].transform(
    lambda x: x - x.shift(5)
).round(2)

df["composite_trend"] = df.groupby("ticker")["composite"].transform(
    lambda x: x - x.shift(5)
).round(2)

df["momentum_5"] = df.groupby("ticker")["close"].transform(
    lambda x: (x / x.shift(5) - 1) * 100
).round(2)

def state_duration(series):
    duration = []
    count = 0
    prev = None
    for val in series:
        if val == prev:
            count += 1
        else:
            count = 1
        duration.append(count)
        prev = val
    return pd.Series(duration, index=series.index)

df["wl_duration"] = df.groupby("ticker")["wl_state"].transform(state_duration)



# Save
df.to_parquet("data/stock_vsa.parquet", engine="pyarrow", index=False)

# Show score distribution
print("Score distribution:")
print(df["composite"].value_counts().sort_index().to_string())
print()
print(f"Score range: {df['composite'].min()} to {df['composite'].max()}")
