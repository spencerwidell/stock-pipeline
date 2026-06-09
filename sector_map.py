# Ticker to parent ETF mapping for top-down analysis
# Each stock maps to its most relevant sub-industry ETF
# and broad market benchmark

SECTOR_MAP = {
    # Semiconductors -> SMH
    "NVDA": {"sector_etf": "SMH", "broad_etf": "QQQ"},
    "AVGO": {"sector_etf": "SMH", "broad_etf": "QQQ"},
    "TSM":  {"sector_etf": "SMH", "broad_etf": "QQQ"},

    # Software -> IGV
    "MSFT": {"sector_etf": "IGV", "broad_etf": "QQQ"},
    "CRM":  {"sector_etf": "IGV", "broad_etf": "QQQ"},
    "NOW":  {"sector_etf": "IGV", "broad_etf": "QQQ"},
    "ORCL": {"sector_etf": "IGV", "broad_etf": "QQQ"},

    # Cloud/growth tech -> SKYY
    "AMZN": {"sector_etf": "SKYY", "broad_etf": "QQQ"},
    "META": {"sector_etf": "SKYY", "broad_etf": "QQQ"},
    "PLTR": {"sector_etf": "SKYY", "broad_etf": "QQQ"},

    # High-beta growth -> QQQ direct
    "TSLA": {"sector_etf": "QQQ",  "broad_etf": "SPY"},
    "SOFI": {"sector_etf": "KRE",  "broad_etf": "SPY"},
    "IBM":  {"sector_etf": "IGV",  "broad_etf": "SPY"},

    # Small cap consumer/growth -> IWM
    "ELF":  {"sector_etf": "IWM",  "broad_etf": "SPY"},
    "CELH": {"sector_etf": "IWM",  "broad_etf": "SPY"},

    # Financials -> XLF
    "JPM":  {"sector_etf": "XLF",  "broad_etf": "SPY"},

    # Defensive -> XLP
    "PG":   {"sector_etf": "XLP",  "broad_etf": "SPY"},

    # Energy -> XLE
    "XOM":  {"sector_etf": "XLE",  "broad_etf": "SPY"},

    # Gold -> GLD direct
    "GLD":  {"sector_etf": "GLD",  "broad_etf": "SPY"},
}

def get_parent_etfs(ticker):
    """Return sector and broad ETF for a given ticker."""
    return SECTOR_MAP.get(ticker, {"sector_etf": "SPY", "broad_etf": "SPY"})

if __name__ == "__main__":
    print("Ticker -> Sector ETF -> Broad ETF")
    print("=" * 45)
    for ticker, mapping in sorted(SECTOR_MAP.items()):
        print(f"{ticker:<6} -> {mapping['sector_etf']:<6} -> {mapping['broad_etf']}")
