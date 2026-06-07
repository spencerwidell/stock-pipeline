import pandas as pd
import numpy as np

df = pd.read_parquet("data/stock_vsa.parquet")
df = df.sort_values(["ticker", "date"]).reset_index(drop=True)

def compute_widell(df, N):
    def add_states(group):
        h = group["high"].values
        l = group["low"].values
        c = group["close"].values
        n = len(group)

        swing_high = np.zeros(n, dtype=bool)
        swing_low  = np.zeros(n, dtype=bool)

        for i in range(N, n - N):
            if h[i] == h[i-N:i+N+1].max():
                swing_high[i] = True
            if l[i] == l[i-N:i+N+1].min():
                swing_low[i] = True

        resistance = np.full(n, np.nan)
        support    = np.full(n, np.nan)
        last_res = last_sup = np.nan

        for i in range(n):
            if swing_high[i]: last_res = h[i]
            if swing_low[i]:  last_sup = l[i]
            resistance[i] = last_res
            support[i]    = last_sup

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
        group["wl_state"] = states
        return group

    tickers = df["ticker"].values
    result = df.groupby("ticker", group_keys=False).apply(add_states)
    result["ticker"] = tickers
    return result

print("Widell Line Parameter Optimization (5-day forward return):")
print(f"{'N':>4}  {'up_bars':>8}  {'down_bars':>10}  {'up_ret':>8}  {'down_ret':>9}  {'spread':>8}")
print("=" * 58)

for N in [2, 3, 5, 7, 10]:
    temp = compute_widell(df.copy(), N)
    temp["return_5d"] = temp.groupby("ticker")["close"].transform(
        lambda x: (x.shift(-5) / x - 1) * 100)

    up   = temp[temp["wl_state"] == "up"]["return_5d"].mean()
    down = temp[temp["wl_state"] == "down"]["return_5d"].mean()
    up_n = (temp["wl_state"] == "up").sum()
    dn_n = (temp["wl_state"] == "down").sum()

    print(f"{N:>4}  {up_n:>8,}  {dn_n:>10,}  {up:>8.3f}  {down:>9.3f}  {up-down:>8.3f}")
