import os
import requests
import pandas as pd
from datetime import datetime, timezone, timedelta


# ---------------------------------------------------------------------------
# 1. Load the API key from the .env file
# ---------------------------------------------------------------------------
def load_env():
    with open(".env") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            key, value = line.split("=", 1)
            os.environ[key] = value


load_env()
API_KEY = os.environ["POLYGON_API_KEY"]


# ---------------------------------------------------------------------------
# 2. Configuration: which tickers and what date range
# ---------------------------------------------------------------------------
# Ticker list comes from universe.yaml (the single source of truth, edited via
# manage_universe.py). META is excluded here and fetched via the special FB+META
# history splice below — that's a fetch quirk, not a universe-membership thing.
from universe import tickers as _universe_tickers

TICKERS = [t for t in _universe_tickers() if t != "META"]

END_DATE   = datetime.now(timezone.utc).date()
START_DATE = END_DATE - timedelta(days=365 * 6)


# ---------------------------------------------------------------------------
# 3. Fetch daily OHLCV for a single ticker
# ---------------------------------------------------------------------------
def fetch_ticker(ticker, start=None, end=None, label=None):
    s = start or START_DATE
    e = end   or END_DATE
    url = (
        f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/{s}/{e}"
    )
    params = {
        "apiKey":   API_KEY,
        "adjusted": "true",
        "sort":     "asc",
        "limit":    50000,
    }
    response = requests.get(url, params=params)
    data = response.json()

    if data.get("resultsCount", 0) == 0:
        print(f"  {ticker}: no results ({data.get('status', 'unknown')})")
        return []

    display_name = label or ticker
    rows = []
    for bar in data["results"]:
        ts = datetime.fromtimestamp(bar["t"] / 1000, tz=timezone.utc)
        rows.append({
            "ticker": display_name,
            "date":   ts.strftime("%Y-%m-%d"),
            "open":   bar["o"],
            "high":   bar["h"],
            "low":    bar["l"],
            "close":  bar["c"],
            "volume": bar["v"],
        })

    print(f"  {display_name} ({ticker}): {len(rows)} days")
    return rows


# ---------------------------------------------------------------------------
# 4. Fetch all tickers
# ---------------------------------------------------------------------------
print(f"Fetching {len(TICKERS) + 1} tickers from {START_DATE} to {END_DATE}...")

all_rows = []

# Standard tickers
for ticker in TICKERS:
    all_rows.extend(fetch_ticker(ticker))

# META special case:
# FB = correct pre-rebrand history (pre Oct 2021)
# META post-rebrand starts Oct 29 2021 with correct prices
fb_rows   = fetch_ticker("FB",   end="2021-10-28", label="META")
meta_rows = fetch_ticker("META", start="2021-10-29", label="META")
all_rows.extend(fb_rows)
all_rows.extend(meta_rows)


# ---------------------------------------------------------------------------
# 5. Build DataFrame and save
# ---------------------------------------------------------------------------
if not all_rows:
    print("No data fetched. Nothing to save.")
else:
    df = pd.DataFrame(all_rows)
    df["date"] = pd.to_datetime(df["date"])

    # Remove any duplicate META rows from overlap
    df = df.drop_duplicates(subset=["ticker", "date"]).reset_index(drop=True)
    df = df.sort_values(["ticker", "date"]).reset_index(drop=True)

    os.makedirs("data", exist_ok=True)
    df.to_parquet("data/stock_ohlcv.parquet", engine="pyarrow", index=False)

    print(f"\nSaved {len(df)} rows for {df['ticker'].nunique()} tickers "
          f"to data/stock_ohlcv.parquet")

    # Verify META
    meta = df[df["ticker"] == "META"].sort_values("date")
    print(f"\nMETA sanity check:")
    print(f"  First: {meta.iloc[0]['date'].date()}  close={meta.iloc[0]['close']:.2f}")
    print(f"  Last:  {meta.iloc[-1]['date'].date()}  close={meta.iloc[-1]['close']:.2f}")
    print(f"  Rows:  {len(meta)}")
