import pandas as pd
import numpy as np
import mlflow
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import accuracy_score, f1_score
from sklearn.preprocessing import LabelEncoder

# Load
df = pd.read_parquet("data/stock_vsa.parquet")
df = df.sort_values(["ticker", "date"]).reset_index(drop=True)

# Target
df["return_5d"] = df.groupby("ticker")["close"].transform(
    lambda x: x.shift(-5) / x - 1
) * 100

def classify_return(r):
    if pd.isna(r): return None
    if r > 1.0: return "up"
    if r < -1.0: return "down"
    return "flat"

df["target"] = df["return_5d"].apply(classify_return)
df = df.dropna(subset=["target"])

# Encode
le_vsa = LabelEncoder()
le_wl  = LabelEncoder()
le_reg = LabelEncoder()
df["vsa_encoded"]    = le_vsa.fit_transform(df["vsa_label"])
df["wl_encoded"]     = le_wl.fit_transform(df["wl_state"])
df["regime_encoded"] = le_reg.fit_transform(df["regime"])

# Three feature sets to compare
FEATURE_SETS = {
    "ma_only":  ["dist_ma200", "ma200_slope", "channel_pos"],
    "vsa_only": ["vsa_encoded", "score_vsa", "rel_volume", "rel_spread"],
    "widell_only": ["wl_encoded", "score_wl", "composite"],
    "all_features": [
        "wl_encoded", "vsa_encoded", "regime_encoded",
        "composite", "rel_volume", "rel_spread",
        "dist_ma200", "ma200_slope", "channel_pos",
        "score_wl", "score_vsa", "score_regime",
    ],
}

y = df["target"]
tscv = TimeSeriesSplit(n_splits=5)

mlflow.set_experiment("widell_feature_isolation")

print("Feature Set Comparison:")
print("=" * 50)

results = {}

for name, features in FEATURE_SETS.items():
    X = df[features].fillna(0)

    all_preds = []
    all_true  = []

    for train_idx, test_idx in tscv.split(X):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=5,
            min_samples_leaf=50,
            random_state=42,
            class_weight="balanced",
            n_jobs=-1,
        )
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        all_preds.extend(preds)
        all_true.extend(y_test)

    acc = accuracy_score(all_true, all_preds)
    f1  = f1_score(all_true, all_preds, average="weighted")
    results[name] = {"accuracy": acc, "f1": f1}

    with mlflow.start_run(run_name=f"feature_isolation_{name}"):
        mlflow.log_param("feature_set", name)
        mlflow.log_param("features", features)
        mlflow.log_metric("accuracy", acc)
        mlflow.log_metric("f1", f1)

    print(f"{name:20s} accuracy={acc:.3f}  f1={f1:.3f}")

print()
print("Baseline (always predict 'up'): accuracy=0.443")
print("Baseline (random):              accuracy=0.363")
