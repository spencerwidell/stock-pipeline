# Ticker -> parent ETF mapping for top-down / sector-rotation analysis.
#
# The mapping now lives in universe.yaml (single source of truth, edited via
# manage_universe.py). This module reads it and exposes the same SECTOR_MAP /
# SECTOR_ETFS / helpers the rest of the pipeline already depends on.
#
# Each ticker maps to one or more sub-industry "sector" ETFs plus a broad
# market benchmark (QQQ for Nasdaq-heavy growth names, SPY otherwise). A few
# names are dual-mapped (e.g. GEV -> XLI + GRID). Broad/thematic ETFs map to
# themselves so they can be ranked directly in Section A of sector_rotation.py.

from universe import load_universe

# {ticker: {"sector_etfs": [...], "broad_etf": "SPY"|"QQQ"}} — shape preserved
# for back-compat with get_parent_etfs / get_constituents and all callers.
SECTOR_MAP = {
    t: {"sector_etfs": v["sector"], "broad_etf": v["broad"]}
    for t, v in load_universe().items()
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
