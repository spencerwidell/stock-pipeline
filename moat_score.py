"""Moat scores via Claude -> data/moat.parquet.

A durable competitive moat is the core of Spencer's "own high-quality companies"
thesis, but it's a qualitative judgment the price/volume pipeline can't compute.
This asks Claude to rate each company's economic moat, so the narrative alert can
say things like "ISRG has a wide moat — pullbacks are typically buyable" and the
dashboard can show moat alongside the F score.

Per ticker, Claude returns (structured output, schema-validated):
    moat_rating   1-5   (1 = no/!narrow moat, 5 = very wide, durable moat)
    moat_type     network_effects | switching_costs | cost_advantage |
                  intangible_assets | none
    moat_summary  one sentence
    moat_risk     the single biggest threat to the moat

ETFs/funds have no company moat and are skipped (identified via sector_map).

Cadence: moats change slowly — run QUARTERLY, not daily. A built-in staleness
guard (REFRESH_DAYS) means re-running only re-scores names missing or older than a
quarter; pass --force to re-score everything.

Model: claude-opus-4-8 — this is a reasoning-heavy quality call run a few times a
year, so it's worth the better model (the daily narrative alert uses Sonnet).

Usage:
    python moat_score.py            # score new / stale tickers only
    python moat_score.py --force    # re-score every stock
    python moat_score.py --only NVDA,ISRG   # score just these
"""

import os
import sys
import time
import json
from datetime import date

import pandas as pd

from sector_map import SECTOR_ETFS

VSA_PATH      = "data/stock_vsa.parquet"
MOAT_PATH     = "data/moat.parquet"
MODEL         = "claude-opus-4-8"
MAX_TOKENS    = 600
REFRESH_DAYS  = 80      # ~ one quarter; re-score only if older than this
REQUEST_PAUSE = 0.5

# ETFs/funds have no company-level moat — never score these.
NON_COMPANIES = set(SECTOR_ETFS) | {"SPY", "QQQ", "IWM", "GLD"}

MOAT_TYPES = ["network_effects", "switching_costs", "cost_advantage",
              "intangible_assets", "none"]

MOAT_SCHEMA = {
    "type": "object",
    "properties": {
        "moat_rating":  {"type": "integer", "enum": [1, 2, 3, 4, 5]},
        "moat_type":    {"type": "string", "enum": MOAT_TYPES},
        "moat_summary": {"type": "string"},
        "moat_risk":    {"type": "string"},
    },
    "required": ["moat_rating", "moat_type", "moat_summary", "moat_risk"],
    "additionalProperties": False,
}

SYSTEM_PROMPT = """You are an equity analyst assessing economic moats in the \
Morningstar tradition. A moat is a structural, durable competitive advantage that \
lets a company earn returns above its cost of capital for many years.

Rate the moat 1-5:
  5 = very wide, durable moat (entrenched, hard to disrupt for a decade+)
  4 = wide moat
  3 = narrow but real moat
  2 = weak / eroding moat
  1 = no meaningful moat (commoditized, or competes only on price/momentum)

Pick the SINGLE best-fit moat_type:
  network_effects   - value rises with users (platforms, marketplaces, exchanges)
  switching_costs   - costly/painful for customers to leave (enterprise software, ecosystems)
  cost_advantage    - structurally lower costs (scale, process, resource access)
  intangible_assets - brands, patents, regulatory licenses, IP
  none              - no durable moat

Be skeptical and specific. A fast-growing or popular stock is not the same as a \
moaty one. moat_summary: one sentence on the source of the advantage. moat_risk: \
the single biggest threat that could erode it."""


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


def universe_stocks():
    df = pd.read_parquet(VSA_PATH, columns=["ticker"])
    return sorted(t for t in df["ticker"].unique() if t not in NON_COMPANIES)


def load_existing():
    if not os.path.exists(MOAT_PATH):
        return pd.DataFrame(
            columns=["ticker", "moat_rating", "moat_type",
                     "moat_summary", "moat_risk", "scored_at"])
    return pd.read_parquet(MOAT_PATH)


def needs_scoring(ticker, existing, force):
    if force:
        return True
    row = existing[existing["ticker"] == ticker]
    if row.empty:
        return True
    try:
        last = pd.to_datetime(row["scored_at"].iloc[0]).date()
    except Exception:
        return True
    return (date.today() - last).days >= REFRESH_DAYS


def score_ticker(client, ticker):
    """Return a dict of moat fields for `ticker`, or None on failure."""
    resp = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        thinking={"type": "disabled"},
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"Assess the economic moat of the publicly traded company "
                       f"with stock ticker {ticker}.",
        }],
        output_config={"format": {"type": "json_schema", "schema": MOAT_SCHEMA}},
    )
    text = next((b.text for b in resp.content if b.type == "text"), None)
    if not text:
        return None
    data = json.loads(text)
    data["ticker"] = ticker
    return data


def main():
    force = "--force" in sys.argv
    load_env()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY not set — cannot score moats.")
        return

    only = None
    for i, a in enumerate(sys.argv):
        if a == "--only" and i + 1 < len(sys.argv):
            only = {t.strip().upper() for t in sys.argv[i + 1].split(",")}

    import anthropic
    client = anthropic.Anthropic()

    existing = load_existing()
    tickers = universe_stocks()
    if only:
        tickers = [t for t in tickers if t in only]

    todo = [t for t in tickers if needs_scoring(t, existing, force)]
    print(f"{len(tickers)} stocks in scope; {len(todo)} need scoring "
          f"(refresh if >= {REFRESH_DAYS}d old). Model: {MODEL}")
    if not todo:
        print("Nothing to score. Use --force to re-score everything.")
        return

    # Normalize existing rows to plain dicts so they merge cleanly with the
    # freshly-scored dicts below (a mix of Series + dict breaks DataFrame()).
    results = {r["ticker"]: r.to_dict() for _, r in existing.iterrows()}
    scored, failed = 0, []
    for t in todo:
        try:
            row = score_ticker(client, t)
            if row is None:
                failed.append(t)
            else:
                row["scored_at"] = date.today()
                results[t] = row
                scored += 1
                print(f"  {t:<6} {row['moat_rating']}/5 {row['moat_type']:<18} "
                      f"{row['moat_summary'][:70]}")
        except Exception as e:
            failed.append(t)
            print(f"  {t:<6} FAILED: {repr(e)[:120]}")
        time.sleep(REQUEST_PAUSE)

    out = pd.DataFrame(list(results.values()))[
        ["ticker", "moat_rating", "moat_type", "moat_summary", "moat_risk", "scored_at"]
    ].sort_values("ticker")
    os.makedirs(os.path.dirname(MOAT_PATH), exist_ok=True)
    out.to_parquet(MOAT_PATH, engine="pyarrow", index=False)

    print(f"\nWrote {MOAT_PATH}: {scored} scored this run, {len(out)} total.")
    if failed:
        print(f"Failed ({len(failed)}): {', '.join(failed)}")


if __name__ == "__main__":
    main()
