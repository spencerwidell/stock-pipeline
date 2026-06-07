import pandas as pd
import numpy as np
import mlflow
import mlflow.sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import classification_report, accuracy_score, f1_score
from sklearn.preprocessing import LabelEncoder

# Load
df = pd.read_parquet("data/stock_vsa.parquet")
df = df.sort_values(["ticker", "date"]).reset_index(drop=True)

# Build target: 5-day forward return bucketed into 3 classes
df["return_5d"] = df.groupby("ticker")["close"].transform(
    lambda x: x.shift(-5) / x - 1
) * 100

def classify_return(r):
    if pd.isna(r):
        return None
    if r > 1.0:
        return "up"
    if r < -1.0:
        return "down"
    return "flat"

df["target"] = df["return_5d"].apply(classify_return)
df = df.dropna(subset=["target"])

# Encode categorical features
le_wl    = LabelEncoder()
le_vsa   = LabelEncoder()
le_reg   = LabelEncoder()

df["wl_encoded"]     = le_wl.fit_transform(df["wl_state"])
df["vsa_encoded"]    = le_vsa.fit_transform(df["vsa_label"])
df["regime_encoded"] = le_reg.fit_transform(df["regime"])

# Feature matrix
FEATURES = [
    "wl_encoded", "vsa_encoded", "regime_encoded",
    "composite", "rel_volume", "rel_spread",
    "dist_ma200", "ma200_slope", "channel_pos",
    "score_wl", "score_vsa", "score_regime",
]

X = df[FEATURES].fillna(0)
y = df["target"]

# Hyperparameters
PARAMS = {
    "n_estimators":    100,
    "max_depth":       5,
    "min_samples_leaf": 50,
    "random_state":    42,
    "class_weight":    "balanced",
    "n_splits":        5,
}

# MLflow experiment
mlflow.set_experiment("widell_vsa_classifier")

with mlflow.start_run(run_name="random_forest_v1"):

    mlflow.log_params(PARAMS)
    mlflow.log_param("features", FEATURES)
    mlflow.log_param("target_thresholds", "up>1%, down<-1%")
    mlflow.log_param("n_samples", len(df))

    tscv = TimeSeriesSplit(n_splits=PARAMS["n_splits"])

    all_preds = []
    all_true  = []
    fold_accs = []

    print("Time Series Cross-Validation:")
    print("=" * 50)

    for fold, (train_idx, test_idx) in enumerate(tscv.split(X)):
        print(f"\nFold {fold+1}/{PARAMS['n_splits']} "
              f"— train: {len(train_idx):,} bars, test: {len(test_idx):,} bars")

        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

        model = RandomForestClassifier(
            n_estimators=PARAMS["n_estimators"],
            max_depth=PARAMS["max_depth"],
            min_samples_leaf=PARAMS["min_samples_leaf"],
            random_state=PARAMS["random_state"],
            class_weight=PARAMS["class_weight"],
            verbose=1,
            n_jobs=-1,
        )
        model.fit(X_train, y_train)
        preds = model.predict(X_test)

        acc = accuracy_score(y_test, preds)
        fold_accs.append(acc)
        all_preds.extend(preds)
        all_true.extend(y_test)

        print(f"Fold {fold+1} accuracy: {acc:.3f}")
        mlflow.log_metric(f"fold_{fold+1}_accuracy", acc)

    # Overall metrics
    overall_acc = accuracy_score(all_true, all_preds)
    overall_f1  = f1_score(all_true, all_preds, average="weighted")

    mlflow.log_metric("overall_accuracy", overall_acc)
    mlflow.log_metric("overall_f1",       overall_f1)
    mlflow.log_metric("mean_fold_accuracy", np.mean(fold_accs))

    print("\n" + "=" * 50)
    print("Overall Classification Report:")
    print(classification_report(all_true, all_preds))

    # Feature importance from last fold
    importances = pd.Series(model.feature_importances_, index=FEATURES)
    importances_sorted = importances.sort_values(ascending=False)
    print("Feature Importances:")
    print(importances_sorted.to_string())

    # Log feature importances
    for feat, imp in importances_sorted.items():
        mlflow.log_metric(f"importance_{feat}", imp)

    # Save model
    mlflow.sklearn.log_model(model, "random_forest_model")

    print(f"\nMLflow run complete.")
    print(f"Overall accuracy: {overall_acc:.3f}")
    print(f"Overall F1:       {overall_f1:.3f}")
