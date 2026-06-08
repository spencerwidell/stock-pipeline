import pandas as pd
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import accuracy_score, f1_score
import mlflow

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {DEVICE}")

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
    if r > 1.0: return 2   # outperform
    if r < -1.0: return 0  # underperform
    return 1               # inline

df["target"] = df["alpha_5d"].apply(classify)
df = df.dropna(subset=["target"])
df["target"] = df["target"].astype(int)

# Encode
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
    "rsi_trend", "composite_trend", "momentum_5", "wl_duration",
]

SEQ_LEN = 20  # look back 20 bars

class SequenceDataset(Dataset):
    def __init__(self, X, y):
        self.X = torch.tensor(X, dtype=torch.float32)
        self.y = torch.tensor(y, dtype=torch.long)

    def __len__(self):
        return len(self.y)

    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]

class LSTMClassifier(nn.Module):
    def __init__(self, input_size, hidden_size=64, num_layers=2, num_classes=3):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers,
                            batch_first=True, dropout=0.3)
        self.fc = nn.Linear(hidden_size, num_classes)

    def forward(self, x):
        out, _ = self.lstm(x)
        out = self.fc(out[:, -1, :])  # last timestep
        return out

def make_sequences(X_arr, y_arr, seq_len):
    Xs, ys = [], []
    for i in range(seq_len, len(X_arr)):
        Xs.append(X_arr[i-seq_len:i])
        ys.append(y_arr[i])
    return np.array(Xs), np.array(ys)

# Time-based train/test split (80/20)
tickers = df["ticker"].unique()
all_preds = []
all_true  = []

mlflow.set_experiment("widell_lstm")

with mlflow.start_run(run_name="lstm_seq20_hidden64"):
    mlflow.log_param("seq_len", SEQ_LEN)
    mlflow.log_param("hidden_size", 64)
    mlflow.log_param("num_layers", 2)
    mlflow.log_param("features", FEATURES)

    for ticker in tickers:
        tdf = df[df["ticker"] == ticker].copy()
        if len(tdf) < SEQ_LEN + 50:
            continue

        X = tdf[FEATURES].fillna(0).values
        y = tdf["target"].values

        # Scale per ticker
        scaler = StandardScaler()
        X = scaler.fit_transform(X)

        # Split 80/20 chronologically
        split = int(len(X) * 0.8)
        X_train, X_test = X[:split], X[split:]
        y_train, y_test = y[:split], y[split:]

        X_train_seq, y_train_seq = make_sequences(X_train, y_train, SEQ_LEN)
        X_test_seq,  y_test_seq  = make_sequences(X_test,  y_test,  SEQ_LEN)

        if len(X_test_seq) < 10:
            continue

        train_ds = SequenceDataset(X_train_seq, y_train_seq)
        test_ds  = SequenceDataset(X_test_seq,  y_test_seq)

        train_dl = DataLoader(train_ds, batch_size=32, shuffle=False)
        test_dl  = DataLoader(test_ds,  batch_size=32, shuffle=False)

        model = LSTMClassifier(input_size=len(FEATURES)).to(DEVICE)
        optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
        criterion = nn.CrossEntropyLoss()

        # Train
        model.train()
        for epoch in range(20):
            for xb, yb in train_dl:
                xb, yb = xb.to(DEVICE), yb.to(DEVICE)
                optimizer.zero_grad()
                loss = criterion(model(xb), yb)
                loss.backward()
                optimizer.step()

        # Evaluate
        model.eval()
        preds = []
        with torch.no_grad():
            for xb, yb in test_dl:
                xb = xb.to(DEVICE)
                out = model(xb)
                preds.extend(out.argmax(dim=1).cpu().numpy())

        all_preds.extend(preds)
        all_true.extend(y_test_seq)
        print(f"  {ticker}: {len(y_test_seq)} test bars")

    label_map = {0: "underperform", 1: "inline", 2: "outperform"}
    preds_str = [label_map[p] for p in all_preds]
    true_str  = [label_map[t] for t in all_true]

    acc = accuracy_score(true_str, preds_str)
    f1  = f1_score(true_str, preds_str, average="weighted")

    mlflow.log_metric("accuracy", acc)
    mlflow.log_metric("f1", f1)

    print(f"\nLSTM Results:")
    print(f"Accuracy: {acc:.3f}")
    print(f"F1:       {f1:.3f}")
    print(f"Naive baseline:    0.368")
    print(f"XGBoost best:      0.417")
