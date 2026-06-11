"""Manage the tracked universe — add / remove / list tickers in universe.yaml.

universe.yaml is the single source of truth for what the pipeline fetches and
scores (read by fetch_stock.py and sector_map.py). This is the one command to
adjust course — add a name to start scoring it, remove one to stop.

Design (per Session 34 decisions):
  - Update-only by default. --add / --remove just edit universe.yaml; the new
    ticker gets its 6-year backfill + signals on the next `run_daily.sh`. Pass
    --run to kick the full pipeline immediately (slow — re-runs the whole thing).
  - No core/watchlist tiers. "Owned" is derived from holdings.yaml (one source
    of truth for positions); --list marks owned names from there.

Examples:
  python manage_universe.py --list
  python manage_universe.py --add GEV --sector XLI,GRID --broad SPY
  python manage_universe.py --add SMR --sector URA          # broad defaults SPY
  python manage_universe.py --remove BIDU                   # also purges its parquet rows
  python manage_universe.py --add NBIS --sector IGV --broad QQQ --run
"""

import argparse
import os
import subprocess
import sys

import pandas as pd

import universe

HOLDINGS_PATH = "holdings.yaml"
# Parquets a removed ticker should be purged from so it stops showing up.
DATA_PARQUETS = [
    "data/stock_ohlcv.parquet",
    "data/stock_vsa.parquet",
    "data/earnings.parquet",
    "data/moat.parquet",
]


def load_holdings():
    """holdings.yaml -> {TICKER: 'weight'}. Empty if absent/unreadable."""
    if not os.path.exists(HOLDINGS_PATH):
        return {}
    try:
        import yaml
        with open(HOLDINGS_PATH) as f:
            raw = yaml.safe_load(f) or {}
        return {str(k).upper(): str(v).strip() for k, v in raw.items() if v is not None}
    except Exception:
        return {}


def parse_sector(s):
    return [x.strip().upper() for x in (s or "").split(",") if x.strip()]


def cmd_list():
    uni = universe.load_universe()
    holdings = load_holdings()
    owned = {t for t in holdings if t != "CASH"}
    print(f"Universe — {len(uni)} tickers "
          f"({len(owned & set(uni))} owned, {len(set(uni) - owned)} watchlist)\n")
    print(f"{'Ticker':<7} {'Sector ETF(s)':<16} {'Broad':<6} {'Held'}")
    print("-" * 44)
    for t in sorted(uni):
        v = uni[t]
        sect = "+".join(v["sector"]) or "—"
        held = f"💼 {holdings[t]}" if t in owned else ""
        print(f"{t:<7} {sect:<16} {v['broad']:<6} {held}")


def cmd_add(ticker, sector, broad):
    ticker = ticker.upper()
    broad = (broad or "SPY").upper()
    sector = parse_sector(sector)
    if broad not in ("SPY", "QQQ"):
        print(f"⚠️  --broad is usually SPY or QQQ (got {broad}); using it anyway.")

    uni = universe.load_universe()
    action = "Updated" if ticker in uni else "Added"
    uni[ticker] = {"sector": sector, "broad": broad}
    universe.write_universe(uni)

    sect_str = "+".join(sector) or "(none — won't appear in sector rotation)"
    print(f"{action} {ticker}: sector {sect_str}, broad {broad}. "
          f"Universe now {len(uni)} tickers.")
    if not sector:
        print("   Tip: pass --sector to bucket it (e.g. --sector SMH), or "
              "--sector " + ticker + " if it's itself an ETF.")
    return True


def cmd_remove(ticker):
    ticker = ticker.upper()
    uni = universe.load_universe()
    if ticker not in uni:
        print(f"{ticker} is not in the universe — nothing to remove.")
        return False

    del uni[ticker]
    universe.write_universe(uni)
    print(f"Removed {ticker} from universe.yaml. Universe now {len(uni)} tickers.")

    # Purge its rows from the data parquets so it stops showing in signals/dashboard.
    for path in DATA_PARQUETS:
        if not os.path.exists(path):
            continue
        try:
            df = pd.read_parquet(path)
            if "ticker" not in df.columns:
                continue
            before = len(df)
            df = df[df["ticker"] != ticker]
            removed = before - len(df)
            if removed:
                df.to_parquet(path, engine="pyarrow", index=False)
                print(f"   purged {removed} row(s) from {path}")
        except Exception as e:
            print(f"   could not purge {path}: {e}")

    # Don't touch holdings.yaml — that's the portfolio record. Just warn.
    if ticker in load_holdings():
        print(f"   ⚠️  {ticker} is still in holdings.yaml (you own it). If you sold, "
              f"edit holdings.yaml too.")
    return True


def run_pipeline():
    print("\nRunning full pipeline (this re-fetches and re-scores everything)...")
    rc = subprocess.run(["bash", "scripts/run_daily.sh"]).returncode
    print(f"Pipeline finished (rc={rc}).")


def main():
    ap = argparse.ArgumentParser(description="Manage the tracked ticker universe.")
    ap.add_argument("--add", metavar="TICKER", help="Add (or update) a ticker")
    ap.add_argument("--remove", metavar="TICKER", help="Remove a ticker (purges its parquet rows)")
    ap.add_argument("--list", action="store_true", help="List the universe")
    ap.add_argument("--sector", default="", help="Sector ETF(s) for --add, comma-separated (e.g. XLI,GRID)")
    ap.add_argument("--broad", default="SPY", help="Broad benchmark for --add: SPY or QQQ (default SPY)")
    ap.add_argument("--run", action="store_true", help="After the change, run the full pipeline now")
    args = ap.parse_args()

    actions = [bool(args.add), bool(args.remove), args.list]
    if sum(actions) != 1:
        ap.error("choose exactly one of --add, --remove, or --list")

    if args.list:
        cmd_list()
        return

    changed = cmd_add(args.add, args.sector, args.broad) if args.add \
        else cmd_remove(args.remove)

    if changed and args.run:
        run_pipeline()
    elif changed:
        print("\nNext: run `bash scripts/run_daily.sh` (or wait for the next close "
              "run) to backfill data for the change.")


if __name__ == "__main__":
    main()
