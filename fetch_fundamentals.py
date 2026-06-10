import requests
import pandas as pd
import os
import time
from dotenv import load_dotenv

load_dotenv()
KEY = os.environ["POLYGON_API_KEY"]

TICKERS = [
    "AMZN", "NVDA", "MSFT", "TSLA", "ELF", "CELH", "PLTR", "AVGO",
    "SOFI", "TSM", "NOW", "IBM", "CRM", "ORCL", "SPY", "QQQ", "IWM",
    "JPM", "PG", "XOM", "GLD", "SMH", "IGV", "SKYY", "XLF", "KRE",
    "XLE", "ICLN", "XLV", "XLP", "EEM", "AXON", "PANW", "ZETA", "SNOW",
    "MU", "BE", "ASML", "HOOD", "GOOG", "MSTR", "NFLX", "BKNG", "AMD",
    "AAPL", "FCX", "FANG", "COST", "CAT", "CMI", "CVX", "MELI", "ZS",
    "CRWD", "ALAB", "BIDU", "ANET", "CDNS", "APP", "ISRG", "VRT", "NXE",
    "SMR", "CRDO", "CEG", "DVN", "RTX", "NBIS", "LITE", "GEV", "ARM",
    "GLW", "PWR", "LRCX", "AMAT", "ONDS", "RKLB", "ASTS", "RGTI", "QBTS",
    "IONQ", "SERV", "UEC", "CCJ", "URG", "LEU", "CRWV", "META"
]

# ETFs don't have financials — skip them
ETF_SKIP = {"SPY","QQQ","IWM","SMH","IGV","SKYY","XLF","KRE","XLE",
            "ICLN","XLV","XLP","EEM","GLD"}

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
        }
        rows.append(row)
    return pd.DataFrame(rows)

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
    # EPS growth
    if pd.notna(row["eps_growth_yoy"]):
        if row["eps_growth_yoy"] > 10:   score += 1
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
