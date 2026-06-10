# Ticker -> parent ETF mapping for top-down / sector-rotation analysis.
#
# Each ticker maps to one or more sub-industry "sector" ETFs plus a broad
# market benchmark (QQQ for Nasdaq-heavy growth names, SPY otherwise).
#
# A few names are dual-mapped because they sit in two themes:
#   GEV  -> XLI (industrials) + GRID (electric grid)
#   PWR  -> XLI (industrials) + PAVE (infrastructure)
#
# Broad/thematic ETFs map to themselves so they can be ranked directly in
# Section A of sector_rotation.py.

SECTOR_MAP = {
    # --- Semiconductors -> SMH ------------------------------------------
    "NVDA": {"sector_etfs": ["SMH"], "broad_etf": "QQQ"},
    "AVGO": {"sector_etfs": ["SMH"], "broad_etf": "QQQ"},
    "TSM":  {"sector_etfs": ["SMH"], "broad_etf": "QQQ"},
    "AMD":  {"sector_etfs": ["SMH"], "broad_etf": "QQQ"},
    "MU":   {"sector_etfs": ["SMH"], "broad_etf": "QQQ"},
    "AMAT": {"sector_etfs": ["SMH"], "broad_etf": "QQQ"},
    "LRCX": {"sector_etfs": ["SMH"], "broad_etf": "QQQ"},
    "ASML": {"sector_etfs": ["SMH"], "broad_etf": "QQQ"},
    "ALAB": {"sector_etfs": ["SMH"], "broad_etf": "QQQ"},
    "CRDO": {"sector_etfs": ["SMH"], "broad_etf": "QQQ"},
    "ARM":  {"sector_etfs": ["SMH"], "broad_etf": "QQQ"},

    # --- Software / security -> IGV -------------------------------------
    "MSFT": {"sector_etfs": ["IGV"], "broad_etf": "QQQ"},
    "CRM":  {"sector_etfs": ["IGV"], "broad_etf": "QQQ"},
    "NOW":  {"sector_etfs": ["IGV"], "broad_etf": "QQQ"},
    "ORCL": {"sector_etfs": ["IGV"], "broad_etf": "QQQ"},
    "IBM":  {"sector_etfs": ["IGV"], "broad_etf": "QQQ"},
    "ANET": {"sector_etfs": ["IGV"], "broad_etf": "QQQ"},
    "PANW": {"sector_etfs": ["IGV"], "broad_etf": "QQQ"},
    "CRWD": {"sector_etfs": ["IGV"], "broad_etf": "QQQ"},
    "ZS":   {"sector_etfs": ["IGV"], "broad_etf": "QQQ"},
    "CDNS": {"sector_etfs": ["IGV"], "broad_etf": "QQQ"},
    "SNOW": {"sector_etfs": ["IGV"], "broad_etf": "QQQ"},
    "APP":  {"sector_etfs": ["IGV"], "broad_etf": "QQQ"},
    "PLTR": {"sector_etfs": ["IGV"], "broad_etf": "QQQ"},
    "CRWV": {"sector_etfs": ["IGV"], "broad_etf": "QQQ"},
    "NBIS": {"sector_etfs": ["IGV"], "broad_etf": "QQQ"},

    # --- Communication / consumer tech -> XLC ---------------------------
    "AAPL": {"sector_etfs": ["XLC"], "broad_etf": "QQQ"},
    "GOOG": {"sector_etfs": ["XLC"], "broad_etf": "QQQ"},
    "NFLX": {"sector_etfs": ["XLC"], "broad_etf": "QQQ"},
    "META": {"sector_etfs": ["XLC"], "broad_etf": "QQQ"},
    "ZETA": {"sector_etfs": ["XLC"], "broad_etf": "SPY"},

    # --- Consumer discretionary -> XLY ----------------------------------
    "AMZN": {"sector_etfs": ["XLY"], "broad_etf": "QQQ"},
    "BKNG": {"sector_etfs": ["XLY"], "broad_etf": "QQQ"},
    "MELI": {"sector_etfs": ["XLY"], "broad_etf": "QQQ"},
    "COST": {"sector_etfs": ["XLY"], "broad_etf": "QQQ"},
    "TSLA": {"sector_etfs": ["XLY"], "broad_etf": "QQQ"},
    "ELF":  {"sector_etfs": ["XLY"], "broad_etf": "SPY"},
    "CELH": {"sector_etfs": ["XLY"], "broad_etf": "SPY"},

    # --- Industrials -> XLI (GEV/PWR dual-mapped below) -----------------
    "CAT":  {"sector_etfs": ["XLI"], "broad_etf": "SPY"},
    "CMI":  {"sector_etfs": ["XLI"], "broad_etf": "SPY"},
    "VRT":  {"sector_etfs": ["XLI"], "broad_etf": "SPY"},
    "GEV":  {"sector_etfs": ["XLI", "GRID"], "broad_etf": "SPY"},
    "PWR":  {"sector_etfs": ["XLI", "PAVE"], "broad_etf": "SPY"},

    # --- Aerospace / defense + space / quantum -> ITA -------------------
    "RTX":  {"sector_etfs": ["ITA"], "broad_etf": "SPY"},
    "AXON": {"sector_etfs": ["ITA"], "broad_etf": "SPY"},
    "RKLB": {"sector_etfs": ["ITA"], "broad_etf": "SPY"},
    "ASTS": {"sector_etfs": ["ITA"], "broad_etf": "SPY"},
    "SERV": {"sector_etfs": ["ITA"], "broad_etf": "SPY"},
    "IONQ": {"sector_etfs": ["ITA"], "broad_etf": "SPY"},
    "QBTS": {"sector_etfs": ["ITA"], "broad_etf": "SPY"},
    "RGTI": {"sector_etfs": ["ITA"], "broad_etf": "SPY"},
    "ONDS": {"sector_etfs": ["ITA"], "broad_etf": "SPY"},

    # --- Materials -> XLB ------------------------------------------------
    "FCX":  {"sector_etfs": ["XLB"], "broad_etf": "SPY"},
    "GLW":  {"sector_etfs": ["XLB"], "broad_etf": "SPY"},
    "LITE": {"sector_etfs": ["XLB"], "broad_etf": "SPY"},

    # --- Energy -> XLE ---------------------------------------------------
    "XOM":  {"sector_etfs": ["XLE"], "broad_etf": "SPY"},
    "CVX":  {"sector_etfs": ["XLE"], "broad_etf": "SPY"},
    "DVN":  {"sector_etfs": ["XLE"], "broad_etf": "SPY"},
    "FANG": {"sector_etfs": ["XLE"], "broad_etf": "SPY"},

    # --- Uranium / nuclear -> URA ---------------------------------------
    "CCJ":  {"sector_etfs": ["URA"], "broad_etf": "SPY"},
    "LEU":  {"sector_etfs": ["URA"], "broad_etf": "SPY"},
    "NXE":  {"sector_etfs": ["URA"], "broad_etf": "SPY"},
    "UEC":  {"sector_etfs": ["URA"], "broad_etf": "SPY"},
    "URG":  {"sector_etfs": ["URA"], "broad_etf": "SPY"},
    "CEG":  {"sector_etfs": ["URA"], "broad_etf": "SPY"},
    "SMR":  {"sector_etfs": ["URA"], "broad_etf": "SPY"},

    # --- Clean energy -> ICLN -------------------------------------------
    "BE":   {"sector_etfs": ["ICLN"], "broad_etf": "SPY"},

    # --- Healthcare -> XLV ----------------------------------------------
    "ISRG": {"sector_etfs": ["XLV"], "broad_etf": "SPY"},

    # --- Financials / fintech -> XLF ------------------------------------
    "JPM":  {"sector_etfs": ["XLF"], "broad_etf": "SPY"},
    "SOFI": {"sector_etfs": ["XLF"], "broad_etf": "SPY"},
    "HOOD": {"sector_etfs": ["XLF"], "broad_etf": "SPY"},
    "MSTR": {"sector_etfs": ["XLF"], "broad_etf": "SPY"},

    # --- Consumer staples -> XLP ----------------------------------------
    "PG":   {"sector_etfs": ["XLP"], "broad_etf": "SPY"},

    # --- Gold -> GLD -----------------------------------------------------
    "GLD":  {"sector_etfs": ["GLD"], "broad_etf": "SPY"},

    # --- Emerging markets -> EEM ----------------------------------------
    "BIDU": {"sector_etfs": ["EEM"], "broad_etf": "SPY"},

    # --- Broad / thematic ETFs (map to themselves) ----------------------
    "SPY":  {"sector_etfs": ["SPY"],  "broad_etf": "SPY"},
    "QQQ":  {"sector_etfs": ["QQQ"],  "broad_etf": "QQQ"},
    "IWM":  {"sector_etfs": ["IWM"],  "broad_etf": "SPY"},
    "EEM":  {"sector_etfs": ["EEM"],  "broad_etf": "SPY"},
    "SMH":  {"sector_etfs": ["SMH"],  "broad_etf": "QQQ"},
    "IGV":  {"sector_etfs": ["IGV"],  "broad_etf": "QQQ"},
    "XLE":  {"sector_etfs": ["XLE"],  "broad_etf": "SPY"},
    "XLF":  {"sector_etfs": ["XLF"],  "broad_etf": "SPY"},
    "XLV":  {"sector_etfs": ["XLV"],  "broad_etf": "SPY"},
    "XLP":  {"sector_etfs": ["XLP"],  "broad_etf": "SPY"},
    "KRE":  {"sector_etfs": ["KRE"],  "broad_etf": "SPY"},
    "ICLN": {"sector_etfs": ["ICLN"], "broad_etf": "SPY"},
    "SKYY": {"sector_etfs": ["SKYY"], "broad_etf": "QQQ"},
    "XLK":  {"sector_etfs": ["XLK"],  "broad_etf": "QQQ"},
    "XLI":  {"sector_etfs": ["XLI"],  "broad_etf": "SPY"},
    "XLB":  {"sector_etfs": ["XLB"],  "broad_etf": "SPY"},
    "XLY":  {"sector_etfs": ["XLY"],  "broad_etf": "QQQ"},
    "XLC":  {"sector_etfs": ["XLC"],  "broad_etf": "QQQ"},
    "ITA":  {"sector_etfs": ["ITA"],  "broad_etf": "SPY"},
    "PAVE": {"sector_etfs": ["PAVE"], "broad_etf": "SPY"},
    "GRID": {"sector_etfs": ["GRID"], "broad_etf": "SPY"},
    "URA":  {"sector_etfs": ["URA"],  "broad_etf": "SPY"},
}

# ETFs that serve as a "sector" bucket someone can rotate into. Anything that
# appears as a value in sector_etfs OR maps to itself counts.
SECTOR_ETFS = sorted({
    etf
    for m in SECTOR_MAP.values()
    for etf in m["sector_etfs"]
})


def get_parent_etfs(ticker):
    """Return sector/broad ETFs for a ticker.

    Returns a dict with:
      sector_etf  - primary sector ETF (first in the list; back-compat)
      sector_etfs - full list of sector ETFs (1+ for dual-mapped names)
      broad_etf   - QQQ or SPY benchmark
    Unknown tickers fall back to SPY/SPY.
    """
    m = SECTOR_MAP.get(ticker)
    if m is None:
        return {"sector_etf": "SPY", "sector_etfs": ["SPY"], "broad_etf": "SPY"}
    return {
        "sector_etf": m["sector_etfs"][0],
        "sector_etfs": list(m["sector_etfs"]),
        "broad_etf": m["broad_etf"],
    }


def get_constituents(etf, exclude_self=True):
    """Reverse lookup: all tickers that map to `etf` as a sector ETF.

    By default the ETF's own self-mapping is excluded so the result is just
    the underlying stocks (used by the Section B laggard scan).
    """
    out = []
    for ticker, m in SECTOR_MAP.items():
        if etf in m["sector_etfs"]:
            if exclude_self and ticker == etf:
                continue
            out.append(ticker)
    return sorted(out)


if __name__ == "__main__":
    print("Ticker -> Sector ETF(s) -> Broad ETF")
    print("=" * 50)
    for ticker, m in sorted(SECTOR_MAP.items()):
        sect = "+".join(m["sector_etfs"])
        print(f"{ticker:<6} -> {sect:<12} -> {m['broad_etf']}")

    print()
    print(f"Total mapped tickers: {len(SECTOR_MAP)}")
    print(f"Sector/thematic ETFs ({len(SECTOR_ETFS)}): {', '.join(SECTOR_ETFS)}")
