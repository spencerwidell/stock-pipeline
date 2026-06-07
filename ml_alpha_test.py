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

# SPY benchmark
spy = df[df["ticker"] == "SPY"][["date", "close"]].copy()
spy["spy_return_5d"] = (spy["close"].shift(-5) / spy["close"] - 1) * 100
spy = spy[["date", "spy_return_5d"]]
df = df.merge(spy, on="date", how="left")

# Alpha target
df["return_5d"] = df.groupby("ticker")["close"].transform(
    lambda x: (x.shift(-5) / x - 1) * 100)
df["alpha_5d"] = df["return_5d"] - df["spy_return_5d"]

def classify(r):
    if pd.isna(r): return None
    if r > 1.0: return "outperform"
    if r < -1.0: return "underperform"
    return "inline"

df["target"] = df["alpha_5d"].apply(classify)
df = df.dropna(subset=["target"])

# Encode categoricals
le_vsa = LabelEncoder()
le_wl  = LabelEncoder()
le_reg = LabelEncoder()
df["vsa_encoded"]    = le_vsa.fit_transform(df["vsa_label"])
df["wl_encoded"]     = le_wl.fit_transform(df["wl_state"])
df["regime_encoded"] = le_reg.fit_transform(df["regime"])

# Feature sets
FEATURE_SETS = {
    "widell_only": [
        "wl_encoded", "score_wl", "composite"
    ],
    "new_features": [
        "close_pos", "upper_wick", "lower_wick",
        "effort", "roc_20", "dist_52w_high", "dist_52w_low"
    ],
    "widell_plus_new": [
        "wl_encoded", "score_wl", "composite",
        "close_pos", "upper_wick", "lower_wick",
        "effort", "roc_20", "dist_52w_high", "dist_52w_low",
        "dist_ma200", "ma200_slope", "channel_pos",
    ],
    "all_features": [
        "wl_encoded", "vsa_encoded", "regime_encoded",
        "composite", "rel_volume", "rel_spread",
        "dist_ma200", "ma200_slope", "channel_pos",
        "score_wl", "score_vsa", "score_regime",
        "close_pos", "upper_wick", "lower_wick",
        "effort", "roc_20", "dist_52w_high", "dist_52w_low",
    ],
}

y = df["target"]
tscv = TimeSeriesSplit(n_splits=5)

mlflow.set_experiment("widell_alpha_classifier")

print("Alpha Target (SPY-relative) Feature Comparison:")
print("=" * 55)
print(f"{'Feature Set':<20} {'Accuracy':>10} {'F1':>10}")
print("-" * 55)

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

    with mlflow.start_run(run_name=f"alpha_{name}"):
        mlflow.log_param("feature_set", name)
        mlflow.log_metric("accuracy", acc)
        mlflow.log_metric("f1", f1)

    print(f"{name:<20} {acc:>10.3f} {f1:>10.3f}")

print()
print(f"{'Naive baseline':<20} {'0.368':>10}")
print(f"{'Random baseline':<20} {'0.333':>10}")

# Feature importance from last model
importances = pd.Series(model.feature_importances_,
                        index=FEATURE_SETS["all_features"])
print()
print("Feature Importances (all_features model):")
print(importances.sort_values(ascending=False).to_string())
