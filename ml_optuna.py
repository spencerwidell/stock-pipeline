import pandas as pd
import numpy as np
import mlflow
import optuna
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier

optuna.logging.set_verbosity(optuna.logging.WARNING)

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

le_wl = LabelEncoder()
df["wl_encoded"] = le_wl.fit_transform(df["wl_state"])

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

mlflow.set_experiment("widell_optuna_tuning")

def objective(trial):
    params = {
        "n_estimators":     trial.suggest_int("n_estimators", 100, 600),
        "max_depth":        trial.suggest_int("max_depth", 2, 8),
        "learning_rate":    trial.suggest_float("learning_rate", 0.005, 0.2, log=True),
        "subsample":        trial.suggest_float("subsample", 0.6, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
        "min_child_weight": trial.suggest_int("min_child_weight", 10, 100),
        "gamma":            trial.suggest_float("gamma", 0, 5),
    }

    all_preds = []
    all_true  = []

    for train_idx, test_idx in tscv.split(X):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

        model = XGBClassifier(
            **params,
            random_state=42,
            eval_metric="mlogloss",
            verbosity=0,
            device="cuda",
        )
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        all_preds.extend(preds)
        all_true.extend(y_test)

    return accuracy_score(all_true, all_preds)

print("Running Optuna hyperparameter search (50 trials, GPU)...")
print("This will take a few minutes...")
print()

study = optuna.create_study(direction="maximize")
study.optimize(objective, n_trials=50, show_progress_bar=True)

best = study.best_trial
print(f"\nBest accuracy: {best.value:.3f}")
print(f"Best params:")
for k, v in best.params.items():
    print(f"  {k}: {v}")

# Log best run to MLflow
with mlflow.start_run(run_name="optuna_best"):
    mlflow.log_params(best.params)
    mlflow.log_metric("accuracy", best.value)

print(f"\nNaive baseline: 0.368")
print(f"Previous best:  0.413")
