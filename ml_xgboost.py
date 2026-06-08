import pandas as pd
import numpy as np
import mlflow
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import accuracy_score, f1_score
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier

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

# Encode
le_wl  = LabelEncoder()
le_reg = LabelEncoder()
df["wl_encoded"]     = le_wl.fit_transform(df["wl_state"])
df["regime_encoded"] = le_reg.fit_transform(df["regime"])

# XGBoost needs numeric target
label_map = {"outperform": 2, "inline": 1, "underperform": 0}
reverse_map = {v: k for k, v in label_map.items()}
df["target_num"] = df["target"].map(label_map)

FEATURES = [
    "wl_encoded", "score_wl", "composite",
    "close_pos", "upper_wick", "lower_wick",
    "effort", "roc_20", "dist_52w_high", "dist_52w_low",
    "dist_ma200", "ma200_slope", "channel_pos",
    "rsi_14", "macd_hist", "macd_cross",
    "rsi_trend", "composite_trend", "momentum_5", "wl_duration",
]

X = df[FEATURES].fillna(0)
y_str = df["target"]
y_num = df["target_num"]
tscv = TimeSeriesSplit(n_splits=5)

mlflow.set_experiment("widell_xgboost_comparison")

models = {
    "RandomForest": {
        "model": RandomForestClassifier(
            n_estimators=100, max_depth=5,
            min_samples_leaf=50, random_state=42,
            class_weight="balanced", n_jobs=-1),
        "y": y_str,
        "numeric": False,
    },
    "XGBoost": {
        "model": XGBClassifier(
            n_estimators=200, max_depth=4,
            learning_rate=0.05, subsample=0.8,
            colsample_bytree=0.8, random_state=42,
            eval_metric="mlogloss", verbosity=0,
            device="cuda"),
        "y": y_num,
        "numeric": True,
    },
}

print("Random Forest vs XGBoost (alpha target):")
print("=" * 50)
print(f"{'Model':<15} {'Accuracy':>10} {'F1':>10}")
print("-" * 50)

for name, cfg in models.items():
    all_preds = []
    all_true  = []

    for train_idx, test_idx in tscv.split(X):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train = cfg["y"].iloc[train_idx]
        y_test  = cfg["y"].iloc[test_idx]

        cfg["model"].fit(X_train, y_train)
        preds = cfg["model"].predict(X_test)

        if cfg["numeric"]:
            preds    = [reverse_map[p] for p in preds]
            y_test   = y_test.map(reverse_map)

        all_preds.extend(preds)
        all_true.extend(y_test)

    acc = accuracy_score(all_true, all_preds)
    f1  = f1_score(all_true, all_preds, average="weighted")

    with mlflow.start_run(run_name=name):
        mlflow.log_metric("accuracy", acc)
        mlflow.log_metric("f1", f1)

    print(f"{name:<15} {acc:>10.3f} {f1:>10.3f}")

print()
print(f"{'Naive baseline':<15} {'0.368':>10}")
print(f"{'Random baseline':<15} {'0.333':>10}")

# XGBoost feature importance
print()
print("XGBoost Feature Importances:")
xgb_model = models["XGBoost"]["model"]
importances = pd.Series(xgb_model.feature_importances_, index=FEATURES)
print(importances.sort_values(ascending=False).to_string())
