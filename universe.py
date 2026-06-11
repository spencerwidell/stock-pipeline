"""Single source of truth for the tracked ticker universe.

`universe.yaml` maps each tracked ticker to its sector ETF(s) and a broad
benchmark (SPY/QQQ). This module just loads/writes it; the consumers are:
  - sector_map.py   builds SECTOR_MAP / SECTOR_ETFS from it (the mapping)
  - fetch_stock.py  takes its ticker list from it (what to fetch)
  - manage_universe.py  edits it (--add / --remove)

Format (one compact line per ticker, kept diff-friendly for the CLI):
    NVDA: {sector: [SMH], broad: QQQ}
    SPY:  {sector: [SPY], broad: SPY}    # ETFs self-map
"""

import yaml

UNIVERSE_PATH = "universe.yaml"


def load_universe(path=UNIVERSE_PATH):
    """Return {TICKER: {'sector': [etf,...], 'broad': 'SPY'|'QQQ'}}, normalized."""
    with open(path) as f:
        raw = yaml.safe_load(f) or {}
    out = {}
    for t, v in raw.items():
        v = v or {}
        sector = v.get("sector") or []
        if isinstance(sector, str):
            sector = [sector]
        broad = (v.get("broad") or "SPY")
        out[str(t).upper()] = {
            "sector": [str(s).upper() for s in sector],
            "broad":  str(broad).upper(),
        }
    return out


def tickers(path=UNIVERSE_PATH):
    """Sorted list of all tracked tickers."""
    return sorted(load_universe(path).keys())


def write_universe(d, path=UNIVERSE_PATH):
    """Write the universe back as compact, alphabetically-sorted YAML."""
    lines = [
        "# Tracked universe — single source of truth for fetch_stock.py and",
        "# sector_map.py. Managed by manage_universe.py (--add / --remove).",
        "# Each ticker maps to its sector ETF(s) and a broad benchmark (SPY/QQQ).",
        "# ETFs self-map, e.g.  SPY: {sector: [SPY], broad: SPY}",
        "",
    ]
    for t in sorted(d.keys()):
        v = d[t]
        sector = ", ".join(v.get("sector") or [])
        broad  = v.get("broad") or "SPY"
        lines.append(f"{t}: {{sector: [{sector}], broad: {broad}}}")
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")
