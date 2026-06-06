import os
import time
import requests
import pandas as pd
from datetime import datetime, timezone, timedelta


# ---------------------------------------------------------------------------
# 1. Load the API key from the .env file
# ---------------------------------------------------------------------------
# We keep secrets out of the code. .env holds POLYGON_API_KEY=... and is listed
# in .gitignore, so the key is never committed. This reads each line into the
# process environment so os.environ can pick it up below.
def load_env():
    with open(".env") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue  # skip blank lines and comments
            key, value = line.split("=", 1)
            os.environ[key] = value


load_env()
API_KEY = os.environ["POLYGON_API_KEY"]


# ---------------------------------------------------------------------------
# 2. Configuration: which tickers and what date range
# ---------------------------------------------------------------------------
TICKERS = [
    "AMZN", "NVDA", "MSFT", "META", "TSLA",
    "ELF", "CELH", "PLTR", "AVGO", "SOFI",
    "TSM", "NOW", "IBM", "CRM", "ORCL",
]

# Last 2 years. The market is closed on weekends/holidays, so the API simply
# returns fewer rows than 730 — that's expected, not an error.
END_DATE = datetime.now(timezone.utc).date()
START_DATE = END_DATE - timedelta(days=2*365)


# ---------------------------------------------------------------------------
# 3. Fetch daily OHLCV for a single ticker
# ---------------------------------------------------------------------------
# Uses Polygon's "aggregates" endpoint, which returns one bar per day across a
# date range. Returns a list of row dicts (one per trading day), or an empty
# list if the request failed or returned nothing.
def fetch_ticker(ticker):
    url = (
        f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/"
        f"{START_DATE}/{END_DATE}"
    )
    params = {
        "apiKey": API_KEY,
        "adjusted": "true",   # adjust for splits/dividends
        "sort": "asc",        # oldest day first
        "limit": 50000,       # plenty for 2 years of daily bars
    }

    response = requests.get(url, params=params)
    data = response.json()

    # resultsCount tells us how many bars came back. 0 means no data (bad
    # ticker, no trading days, or an API issue) — skip it.
    if data.get("resultsCount", 0) == 0:
        print(f"  {ticker}: no results ({data.get('status', 'unknown status')})")
        return []

    # Reshape each raw bar into a clean, named row. Polygon uses short keys:
    #   t = timestamp (ms), o/h/l/c = open/high/low/close, v = volume
    rows = []
    for bar in data["results"]:
        ts = datetime.fromtimestamp(bar["t"] / 1000, tz=timezone.utc)
        rows.append({
            "ticker": ticker,
            "date": ts.strftime("%Y-%m-%d"),
            "open": bar["o"],
            "high": bar["h"],
            "low": bar["l"],
            "close": bar["c"],
            "volume": bar["v"],
        })

    print(f"  {ticker}: {len(rows)} days")
    return rows


# ---------------------------------------------------------------------------
# 4. Loop over every ticker and collect all rows
# ---------------------------------------------------------------------------
# We accumulate rows from all tickers into one flat list, then build a single
# DataFrame. We add a 200ms sleep between requests to be polite to the API.
print(f"Fetching {len(TICKERS)} tickers from {START_DATE} to {END_DATE}...")

all_rows = []
for i, ticker in enumerate(TICKERS, start=1):
    print(f"[{i}/{len(TICKERS)}] Fetching {ticker}...")
    all_rows.extend(fetch_ticker(ticker))

    # Sleep between requests to be polite to the API, except after the last one
    if i < len(TICKERS):
        time.sleep(3)


# ---------------------------------------------------------------------------
# 5. Build a DataFrame and save it as Parquet
# ---------------------------------------------------------------------------
# A single tidy table: one row per (ticker, date). Parquet is a compressed,
# columnar format — far smaller and faster to read than CSV, and it preserves
# data types (dates stay dates, numbers stay numbers).
if not all_rows:
    print("No data fetched for any ticker. Nothing to save.")
else:
    df = pd.DataFrame(all_rows)
    df["date"] = pd.to_datetime(df["date"])  # store as real dates, not strings

    # Make sure the data/ directory exists before writing into it.
    os.makedirs("data", exist_ok=True)
    output_path = "data/stock_ohlcv_2yr.parquet"

    # pyarrow is the engine pandas uses to write Parquet.
    df.to_parquet(output_path, engine="pyarrow", index=False)

    print(f"\nSaved {len(df)} rows for {df['ticker'].nunique()} tickers "
          f"to {output_path}")
