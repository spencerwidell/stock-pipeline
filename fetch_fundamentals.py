import requests
import pandas as pd
import os
import time
from dotenv import load_dotenv

from universe import tickers as universe_tickers
from sector_map import SECTOR_ETFS

load_dotenv()
KEY = os.environ["POLYGON_API_KEY"]

# Tickers come from universe.yaml (single source of truth). ETFs have no company
# financials, so skip them (same convention as moat_score.py).
NON_COMPANIES = set(SECTOR_ETFS) | {"SPY", "QQQ", "IWM", "GLD"}
TICKERS = [t for t in universe_tickers() if t not in NON_COMPANIES]
ETF_SKIP = NON_COMPANIES

def get_financials(ticker, limit=8):
    url = (f"https://api.polygon.io/vX/reference/financials"
           f"?ticker={ticker}&limit={limit}&timeframe=quarterly"
           f"&apiKey={KEY}")
    r = requests.get(url)
    if r.status_code != 200:
        return None
    data = r.json()
    if not data.get("results"):
        return None
    return data["results"]

def extract_metrics(results):
    rows = []
    for r in results:
        inc = r["financials"].get("income_statement", {})
        cf  = r["financials"].get("cash_flow_statement", {})
        row = {
            "fiscal_period": r.get("fiscal_period"),
            "fiscal_year":   r.get("fiscal_year"),
            "end_date":      r.get("end_date"),
            "revenue":       inc.get("revenues", {}).get("value"),
            "gross_profit":  inc.get("gross_profit", {}).get("value"),
            "operating_income": inc.get("operating_income_loss", {}).get("value"),
            "net_income":    inc.get("net_income_loss", {}).get("value"),
            "eps_basic":     inc.get("basic_earnings_per_share", {}).get("value"),
            "operating_cf":  cf.get("net_cash_flow_from_operating_activities", {}).get("value"),
            "shares":        inc.get("diluted_average_shares", {}).get("value"),
        }
        rows.append(row)
    return pd.DataFrame(rows)


def ttm_sum(series, n=4):
    """Sum the most recent n values; None if fewer than n or any is missing."""
    vals = series.head(n).tolist()
    if len(vals) < n or any(v is None or pd.isna(v) for v in vals):
        return None
    return sum(vals)

records = []
skipped = []

for ticker in TICKERS:
    if ticker in ETF_SKIP:
        skipped.append(ticker)
        continue

    results = get_financials(ticker)
    if not results:
        print(f"  {ticker}: no data")
        skipped.append(ticker)
        time.sleep(0.1)
        continue

    df = extract_metrics(results)
    df = df.dropna(subset=["revenue"]).reset_index(drop=True)

    if len(df) < 2:
        print(f"  {ticker}: insufficient quarters ({len(df)})")
        skipped.append(ticker)
        time.sleep(0.1)
        continue

    # Most recent quarter
    latest = df.iloc[0]

    # YoY comparisons — find same quarter last year
    rev_yoy = None
    eps_yoy = None
    if len(df) >= 5:
        prior = df.iloc[4]
        if prior["revenue"] and prior["revenue"] != 0:
            rev_yoy = round((latest["revenue"] - prior["revenue"]) / abs(prior["revenue"]) * 100, 1)
        if prior["eps_basic"] and prior["eps_basic"] != 0 and latest["eps_basic"]:
            eps_yoy = round((latest["eps_basic"] - prior["eps_basic"]) / abs(prior["eps_basic"]) * 100, 1)

    # Margins
    gross_margin = None
    op_margin    = None
    if latest["revenue"] and latest["revenue"] > 0:
        if latest["gross_profit"]:
            gross_margin = round(latest["gross_profit"] / latest["revenue"] * 100, 1)
        if latest["operating_income"]:
            op_margin = round(latest["operating_income"] / latest["revenue"] * 100, 1)

    # --- TTM valuation inputs (PE / PEG / P-OCF are computed at display time
    #     against the current price; here we store the per-company financial
    #     inputs that change only quarterly). ---
    ttm_eps = ttm_sum(df["eps_basic"], 4)        # per-share TTM earnings
    ttm_ocf = ttm_sum(df["operating_cf"], 4)     # TTM operating cash flow ($)
    # Polygon's diluted_average_shares is occasionally garbage for a single
    # quarter (e.g. AMZN/ELF report ~1000x too few). Take the median over recent
    # quarters so one bad print can't blow up P/OCF.
    sh_vals = [s for s in df["shares"].head(4).tolist()
               if s is not None and not pd.isna(s) and s > 0]
    shares = float(pd.Series(sh_vals).median()) if sh_vals else None
    # TTM-over-TTM EPS growth (more stable than single-quarter YoY) when 8q exist
    ttm_eps_growth = None
    prior_ttm_eps = ttm_sum(df["eps_basic"].iloc[4:], 4) if len(df) >= 8 else None
    if ttm_eps is not None and prior_ttm_eps not in (None, 0) and prior_ttm_eps > 0:
        ttm_eps_growth = round((ttm_eps - prior_ttm_eps) / prior_ttm_eps * 100, 1)

    records.append({
        "ticker":       ticker,
        "as_of":        latest["end_date"],
        "revenue_B":    round(latest["revenue"] / 1e9, 2) if latest["revenue"] else None,
        "rev_growth_yoy": rev_yoy,
        "gross_margin": gross_margin,
        "op_margin":    op_margin,
        "eps_basic":    latest["eps_basic"],
        "eps_growth_yoy": eps_yoy,
        "operating_cf_B": round(latest["operating_cf"] / 1e9, 2) if latest["operating_cf"] else None,
        # valuation inputs
        "ttm_eps":        round(ttm_eps, 4) if ttm_eps is not None else None,
        "ttm_ocf":        ttm_ocf,
        "shares":         shares,
        "ttm_eps_growth": ttm_eps_growth,
    })
    print(f"  {ticker}: rev=${records[-1]['revenue_B']}B  rev_yoy={rev_yoy}%  gm={gross_margin}%")
    time.sleep(0.12)  # rate limit

print(f"\nFetched {len(records)} tickers, skipped {len(skipped)}")
print(f"Skipped: {skipped}")

fund_df = pd.DataFrame(records)

# Fundamental score (0-5)
def score_fundamentals(row):
    score = 0
    # Revenue growth
    if pd.notna(row["rev_growth_yoy"]):
        if row["rev_growth_yoy"] > 20:   score += 1
    # Gross margin
    if pd.notna(row["gross_margin"]):
        if row["gross_margin"] > 50:     score += 1
    # Operating margin
    if pd.notna(row["op_margin"]):
        if row["op_margin"] > 15:        score += 1
    # EPS growth — prefer the stable TTM figure (a single quarter is too noisy to
    # gate quality on); fall back to the latest-quarter YoY only if TTM is missing.
    eps_growth = (row["ttm_eps_growth"] if pd.notna(row.get("ttm_eps_growth"))
                  else row.get("eps_growth_yoy"))
    if pd.notna(eps_growth):
        if eps_growth > 10:              score += 1
    # Positive operating cash flow
    if pd.notna(row["operating_cf_B"]):
        if row["operating_cf_B"] > 0:    score += 1
    return score

fund_df["fundamental_score"] = fund_df.apply(score_fundamentals, axis=1)

fund_df = fund_df.sort_values("fundamental_score", ascending=False)
print("\nFundamental scores:")
print(fund_df[["ticker","fundamental_score","rev_growth_yoy","gross_margin","op_margin","eps_growth_yoy","operating_cf_B"]].to_string(index=False))

fund_df.to_parquet("data/fundamentals.parquet", index=False)
print("\nSaved to data/fundamentals.parquet")
