import pandas as pd
import numpy as np
import mlflow
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

label_map = {"outperform": 2, "inline": 1, "underperform": 0}
reverse_map = {v: k for k, v in label_map.items()}
df["target_num"] = df["target"].map(label_map)

le_wl  = LabelEncoder()
le_reg = LabelEncoder()
df["wl_encoded"]     = le_wl.fit_transform(df["wl_state"])
df["regime_encoded"] = le_reg.fit_transform(df["regime"])

FEATURES = [
    "wl_encoded", "score_wl", "composite",
    "close_pos", "upper_wick", "lower_wick",
    "effort", "roc_20", "dist_52w_high", "dist_52w_low",
    "dist_ma200", "ma200_slope", "channel_pos",
    "rsi_14", "macd_hist", "macd_cross",
]

X = df[FEATURES].fillna(0)
y = df["target_num"]
tscv = TimeSeriesSplit(n_splits=5)

param_grid = [
    {"n_estimators": 200, "max_depth": 3, "learning_rate": 0.05,  "subsample": 0.8, "colsample_bytree": 0.8},
    {"n_estimators": 200, "max_depth": 4, "learning_rate": 0.05,  "subsample": 0.8, "colsample_bytree": 0.8},
    {"n_estimators": 200, "max_depth": 4, "learning_rate": 0.01,  "subsample": 0.8, "colsample_bytree": 0.8},
    {"n_estimators": 500, "max_depth": 4, "learning_rate": 0.01,  "subsample": 0.8, "colsample_bytree": 0.8},
    {"n_estimators": 200, "max_depth": 6, "learning_rate": 0.05,  "subsample": 0.7, "colsample_bytree": 0.7},
    {"n_estimators": 500, "max_depth": 3, "learning_rate": 0.01,  "subsample": 0.9, "colsample_bytree": 0.9},
    {"n_estimators": 300, "max_depth": 4, "learning_rate": 0.03,  "subsample": 0.8, "colsample_bytree": 0.8},
]

mlflow.set_experiment("widell_xgboost_tuning")

print("XGBoost Hyperparameter Tuning (GPU, alpha target):")
print("=" * 75)
print(f"{'n_est':>6}  {'depth':>6}  {'lr':>6}  {'sub':>5}  {'col':>5}  {'accuracy':>10}  {'f1':>8}")
print("-" * 75)

best_acc = 0
best_params = None

for params in param_grid:
    all_preds = []
    all_true  = []

    for train_idx, test_idx in tscv.split(X):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

        model = XGBClassifier(
            n_estimators=params["n_estimators"],
            max_depth=params["max_depth"],
            learning_rate=params["learning_rate"],
            subsample=params["subsample"],
            colsample_bytree=params["colsample_bytree"],
            random_state=42,
            eval_metric="mlogloss",
            verbosity=0,
            device="cuda",
        )
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        preds_str = [reverse_map[p] for p in preds]
        true_str  = y_test.map(reverse_map)
        all_preds.extend(preds_str)
        all_true.extend(true_str)

    acc = accuracy_score(all_true, all_preds)
    f1  = f1_score(all_true, all_preds, average="weighted")

    if acc > best_acc:
        best_acc = acc
        best_params = params

    with mlflow.start_run(run_name=f"xgb_d{params['max_depth']}_lr{params['learning_rate']}"):
        mlflow.log_params(params)
        mlflow.log_metric("accuracy", acc)
        mlflow.log_metric("f1", f1)

    print(f"{params['n_estimators']:>6}  {params['max_depth']:>6}  "
          f"{params['learning_rate']:>6}  {params['subsample']:>5}  "
          f"{params['colsample_bytree']:>5}  {acc:>10.3f}  {f1:>8.3f}")

print()
print(f"Best accuracy: {best_acc:.3f}")
print(f"Best params: {best_params}")
print(f"Naive baseline: 0.368")
