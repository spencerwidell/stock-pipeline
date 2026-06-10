"""Fetch the next earnings date per ticker -> data/earnings.parquet.

Earnings matter for entry timing: a high-conviction name reporting in a few days
is a reason to wait, not buy. This adds a forward earnings date for every ticker
in the universe so the alerts/dashboard can flag 🗓️ on names reporting soon.

Source: yfinance (`Ticker.calendar['Earnings Date']`). Polygon's forward earnings
live behind the Benzinga add-on, which this plan's Polygon tier doesn't include;
yfinance is the free path to *future* earnings dates. ETFs (SPY, XLF, ...) have
no earnings and are skipped silently.

Cadence: earnings dates barely move week to week, so this only needs a weekly
refresh. The script has a built-in staleness guard (REFRESH_DAYS) so it's safe to
call every day from a pipeline — it no-ops until the data is stale, then refetches.

Output schema (data/earnings.parquet):
    ticker, next_earnings_date (date), fetched_at (date)

Usage:
    python fetch_earnings.py           # refetch only if stale (>= REFRESH_DAYS old)
    python fetch_earnings.py --force   # refetch now regardless of age
"""

import os
import sys
import time
import warnings
from datetime import date

import pandas as pd

VSA_PATH      = "data/stock_vsa.parquet"
EARNINGS_PATH = "data/earnings.parquet"
REFRESH_DAYS  = 6     # refetch only if existing data is at least this old
REQUEST_PAUSE = 0.3   # polite delay between yfinance calls (seconds)


def load_env():
    if not os.path.exists(".env"):
        return
    with open(".env") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            k, v = line.split("=", 1)
            os.environ[k] = v


def universe():
    """Tickers actually tracked, read from the signal parquet (stays in sync)."""
    df = pd.read_parquet(VSA_PATH, columns=["ticker"])
    return sorted(df["ticker"].unique().tolist())


def is_stale():
    """True if earnings.parquet is missing or older than REFRESH_DAYS."""
    if not os.path.exists(EARNINGS_PATH):
        return True
    try:
        e = pd.read_parquet(EARNINGS_PATH)
        if "fetched_at" not in e.columns or e.empty:
            return True
        last = pd.to_datetime(e["fetched_at"]).max().date()
        return (date.today() - last).days >= REFRESH_DAYS
    except Exception:
        return True


def next_earnings_date(ticker):
    """Earliest upcoming earnings date for `ticker`, or None."""
    import yfinance as yf
    try:
        cal = yf.Ticker(ticker).calendar
    except Exception:
        return None
    if not isinstance(cal, dict):
        return None
    dates = cal.get("Earnings Date")
    if not dates:
        return None
    # yfinance returns a list of datetime.date (sometimes a confirmed date plus a
    # range). Take the earliest one that is today or later.
    today = date.today()
    future = sorted(d for d in dates if d and d >= today)
    return future[0] if future else (sorted(dates)[0] if dates else None)


def main():
    force = "--force" in sys.argv
    load_env()

    if not force and not is_stale():
        print(f"{EARNINGS_PATH} is fresh (< {REFRESH_DAYS} days old) — skipping. "
              f"Use --force to refetch.")
        return

    warnings.filterwarnings("ignore")
    tickers = universe()
    print(f"Fetching earnings dates for {len(tickers)} tickers...")

    rows = []
    found = 0
    for t in tickers:
        d = next_earnings_date(t)
        rows.append({"ticker": t, "next_earnings_date": d})
        if d is not None:
            found += 1
        time.sleep(REQUEST_PAUSE)

    out = pd.DataFrame(rows)
    out["fetched_at"] = date.today()
    os.makedirs(os.path.dirname(EARNINGS_PATH), exist_ok=True)
    out.to_parquet(EARNINGS_PATH, engine="pyarrow", index=False)
    print(f"Wrote {EARNINGS_PATH}: {found}/{len(tickers)} tickers have a date.")

    # Report names reporting within the next week.
    today = date.today()
    soon = out.dropna(subset=["next_earnings_date"]).copy()
    soon["days"] = soon["next_earnings_date"].apply(lambda d: (d - today).days)
    soon = soon[(soon["days"] >= 0) & (soon["days"] <= 7)].sort_values("days")
    if len(soon):
        print(f"\n🗓️  Earnings within 7 days ({len(soon)}):")
        for _, r in soon.iterrows():
            print(f"  {r['ticker']:<6} {r['next_earnings_date']}  (in {int(r['days'])}d)")
    else:
        print("\nNo earnings within 7 days.")


if __name__ == "__main__":
    main()
