import requests
import pandas as pd
import os
import time
from statistics import median
from dotenv import load_dotenv

from universe import tickers as universe_tickers
from sector_map import SECTOR_ETFS, get_parent_etfs
import business_model

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
        fin = r["financials"]
        inc = fin.get("income_statement", {})
        cf  = fin.get("cash_flow_statement", {})
        bs  = fin.get("balance_sheet", {})
        def v(stmt, key):
            return stmt.get(key, {}).get("value")
        row = {
            "fiscal_period": r.get("fiscal_period"),
            "fiscal_year":   r.get("fiscal_year"),
            "end_date":      r.get("end_date"),
            "revenue":       v(inc, "revenues"),
            "gross_profit":  v(inc, "gross_profit"),
            "operating_income": v(inc, "operating_income_loss"),
            "net_income":    v(inc, "net_income_loss"),
            "eps_basic":     v(inc, "basic_earnings_per_share"),
            "operating_cf":  v(cf, "net_cash_flow_from_operating_activities"),
            "shares":        v(inc, "diluted_average_shares"),
            # balance sheet — enables ROE / ROA / debt-to-equity (one pull, capture all)
            "equity":        v(bs, "equity_attributable_to_parent") or v(bs, "equity"),
            "assets":        v(bs, "assets"),
            "long_term_debt": v(bs, "long_term_debt"),
            # bank / extra income lines — efficiency ratio, dividends
            "noninterest_expense": v(inc, "noninterest_expense"),
            "dividends":     v(inc, "common_stock_dividends"),
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
    # The rubric grades on the stable TTM figure; fall back to single-quarter YoY.
    eps_growth = ttm_eps_growth if ttm_eps_growth is not None else eps_yoy

    # --- Forward EPS projection from our OWN historical run-rate (no analyst feed).
    #     Four YoY readings (each recent quarter vs the same quarter a year prior)
    #     give a bear/base/bull growth band; base = median (robust to one outlier). ---
    eps_q = df["eps_basic"].tolist()
    yoy = []
    if len(eps_q) >= 8:
        for i in range(4):
            base, cur = eps_q[i + 4], eps_q[i]
            if (base is not None and not pd.isna(base) and base > 0
                    and cur is not None and not pd.isna(cur)):
                yoy.append((cur - base) / base * 100)
    if len(yoy) >= 3:
        eps_g_bear, eps_g_base, eps_g_bull = (round(min(yoy), 1),
                                              round(median(yoy), 1), round(max(yoy), 1))
    elif ttm_eps_growth is not None:                 # fallback: one reading ± a spread
        eps_g_base = ttm_eps_growth
        eps_g_bear, eps_g_bull = round(ttm_eps_growth - 15, 1), round(ttm_eps_growth + 15, 1)
    else:
        eps_g_bear = eps_g_base = eps_g_bull = None

    # --- Balance-sheet-derived ratios (ROE / ROA / efficiency / debt-to-equity) ---
    ttm_net_income = ttm_sum(df["net_income"], 4)
    ttm_revenue    = ttm_sum(df["revenue"], 4)
    ttm_nie        = ttm_sum(df["noninterest_expense"], 4)
    equity = latest.get("equity"); assets = latest.get("assets")
    ltd    = latest.get("long_term_debt")
    roe = (round(ttm_net_income / equity * 100, 1)
           if ttm_net_income is not None and equity and equity > 0 else None)
    roa = (round(ttm_net_income / assets * 100, 1)
           if ttm_net_income is not None and assets and assets > 0 else None)
    efficiency_ratio = (round(ttm_nie / ttm_revenue * 100, 1)
                        if ttm_nie is not None and ttm_revenue and ttm_revenue > 0 else None)
    debt_to_equity = (round(ltd / equity, 2)
                      if ltd is not None and equity and equity > 0 else None)
    op_margin_prev = None
    if len(df) >= 5:
        p = df.iloc[4]
        if p["revenue"] and p["revenue"] > 0 and p["operating_income"] is not None:
            op_margin_prev = round(p["operating_income"] / p["revenue"] * 100, 1)
    dividends = latest.get("dividends")
    dividend_payer = bool(dividends is not None and not pd.isna(dividends) and dividends != 0)

    # Business archetype — pre_profit is data-driven (non-positive TTM earnings),
    # else sector-ETF-derived (+ a small override list) in business_model.
    sec = get_parent_etfs(ticker)
    sector_etf = sec.get("sector_etf") if isinstance(sec, dict) else None
    archetype = business_model.get_archetype(
        ticker, {"ttm_net_income": ttm_net_income}, sector_etf)

    records.append({
        "ticker":       ticker,
        "as_of":        latest["end_date"],
        "archetype":    archetype,
        "revenue_B":    round(latest["revenue"] / 1e9, 2) if latest["revenue"] else None,
        "rev_growth_yoy": rev_yoy,
        "gross_margin": gross_margin,
        "op_margin":    op_margin,
        "op_margin_prev": op_margin_prev,
        "eps_basic":    latest["eps_basic"],
        "eps_growth_yoy": eps_yoy,
        "eps_growth":   eps_growth,
        "operating_cf_B": round(latest["operating_cf"] / 1e9, 2) if latest["operating_cf"] else None,
        # balance-sheet ratios
        "roe":          roe,
        "roa":          roa,
        "efficiency_ratio": efficiency_ratio,
        "debt_to_equity": debt_to_equity,
        "dividend_payer": dividend_payer,
        "ttm_net_income": round(ttm_net_income, 0) if ttm_net_income is not None else None,
        # valuation inputs
        "ttm_eps":        round(ttm_eps, 4) if ttm_eps is not None else None,
        "ttm_ocf":        ttm_ocf,
        "shares":         shares,
        "ttm_eps_growth": ttm_eps_growth,
        # forward projection (our own run-rate band)
        "eps_growth_bear": eps_g_bear,
        "eps_growth_base": eps_g_base,
        "eps_growth_bull": eps_g_bull,
    })
    print(f"  {ticker}: {archetype} | rev=${records[-1]['revenue_B']}B  "
          f"rev_yoy={rev_yoy}%  gm={gross_margin}%  roe={roe}%")
    time.sleep(0.12)  # rate limit

print(f"\nFetched {len(records)} tickers, skipped {len(skipped)}")
print(f"Skipped: {skipped}")

fund_df = pd.DataFrame(records)

# Fundamental score (0-5) — sector-aware: each name is graded by the rubric for its
# business archetype (software / platform / financial / energy / industrial / staple /
# consumer / pre_profit). See business_model.py.
fund_df["fundamental_score"] = fund_df.apply(
    lambda r: business_model.score_fundamentals(r), axis=1)

fund_df = fund_df.sort_values(["archetype", "fundamental_score"], ascending=[True, False])
print("\nFundamental scores (by archetype):")
print(fund_df[["ticker", "archetype", "fundamental_score", "rev_growth_yoy",
               "op_margin", "roe", "efficiency_ratio", "operating_cf_B"]].to_string(index=False))

fund_df.to_parquet("data/fundamentals.parquet", index=False)
print("\nSaved to data/fundamentals.parquet")
