import pandas as pd

# Load VSA features
df = pd.read_parquet("data/stock_vsa.parquet")

# Thresholds
HIGH_VOL  = 1.5
LOW_VOL   = 0.7
WIDE      = 1.5
NARROW    = 0.7

def classify(row):
    up        = row["direction"] == "up"
    wide      = row["rel_spread"] >= WIDE
    narrow    = row["rel_spread"] <= NARROW
    high_vol  = row["rel_volume"] >= HIGH_VOL
    low_vol   = row["rel_volume"] <= LOW_VOL

    if up and wide and high_vol:
        return "buying_climax"
    if not up and wide and high_vol:
        return "selling_climax"
    if up and narrow and low_vol:
        return "no_demand"
    if not up and narrow and low_vol:
        return "no_supply"
    if up and wide and not low_vol:
        return "effort_up"
    if not up and wide and not low_vol:
        return "effort_down"
    return "neutral"

df["vsa_label"] = df.apply(classify, axis=1)

# Save
df.to_parquet("data/stock_vsa.parquet", engine="pyarrow", index=False)

# Summary
print(df["vsa_label"].value_counts().to_string())
