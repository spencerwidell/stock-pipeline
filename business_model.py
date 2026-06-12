"""Business-model archetypes + sector-aware fundamental scoring.

One software-tuned rubric (rev>20, gross>50, op>15, eps>10, +OCF) mis-scores whole
categories: banks have no "gross margin" (they run on ROE / efficiency ratio), energy
is cyclical (margins swing with the commodity), low-margin-by-design mega-caps
(AMZN, COST) get punished for a model that's actually excellent, and healthcare/
life-sciences compounders (ISRG, DHR, TMO) are penalized for not growing 20%+ like
SaaS when their quality is durable margins + recurring cash. So each name is judged
on the metrics that fit its business.

Archetype is assigned from the ticker's sector ETF (universe.yaml) with a small override
list, EXCEPT a name with non-positive trailing earnings is 'pre_profit' regardless of
sector (you can't judge a pre-profit company on profitability).

All rubrics return a 0-5 score on the SAME scale, so conviction + auto_classify are
unchanged — only the *criteria* differ. Scores read derived fields already stored in
fundamentals.parquet, so the rubric can be re-tuned without re-pulling from Polygon.

See memory sector-aware-fundamentals.
"""

import pandas as pd

# Sector ETF (universe.yaml primary sector) -> archetype.
ETF_ARCHETYPE = {
    # high-margin tech / chips / software
    "SMH": "software", "IGV": "software", "XLK": "software", "SKYY": "software",
    # healthcare / medical devices / life-sciences tools (steady compounders,
    # NOT hypergrowth SaaS — graded on margins/returns/cash, not 20%+ rev growth)
    "XLV": "healthcare",
    # ad / media / communications platforms
    "XLC": "platform",
    # consumer discretionary (cyclical retail / brands)
    "XLY": "consumer",
    # consumer staples
    "XLP": "staple",
    # banks / brokers / financials
    "XLF": "financial", "KRE": "financial",
    # energy + nuclear/uranium utilities + clean energy
    "XLE": "energy", "URA": "energy", "ICLN": "energy",
    # industrials / materials / defense / infrastructure
    "XLI": "industrial", "XLB": "industrial", "ITA": "industrial",
    "PAVE": "industrial", "GRID": "industrial",
    # emerging-market names (often skipped for data anyway)
    "EEM": "consumer",
}

# Names whose economic nature differs from their sector default.
TICKER_OVERRIDE = {
    "AMZN": "platform",     # XLY by GICS, but a cloud + marketplace platform
    "MELI": "platform",     # marketplace + fintech
    "TSLA": "industrial",   # an auto manufacturer (cyclical), not a SaaS name
    "COST": "staple",       # warehouse retail behaves like a staple
    "AAPL": "software",     # hardware + services with software-like margins
}

DEFAULT_ARCHETYPE = "software"


def get_archetype(ticker, row=None, sector_etf=None):
    """Archetype for a ticker. A company that is BOTH unprofitable on a trailing
    basis AND not generating operating cash is 'pre_profit' (can't grade it on
    profitability). A GAAP loss alone does NOT qualify — cash-generative SaaS names
    run GAAP losses from stock-based comp yet are real businesses, so they stay in
    their sector. Else override, else the sector-ETF mapping, else the default."""
    if row is not None:
        ni  = row.get("ttm_net_income")
        ocf = row.get("ttm_ocf")
        ni_neg  = pd.notna(ni) and ni is not None and ni <= 0
        ocf_neg = ocf is None or pd.isna(ocf) or ocf <= 0
        if ni_neg and ocf_neg:
            return "pre_profit"
    if ticker in TICKER_OVERRIDE:
        return TICKER_OVERRIDE[ticker]
    if sector_etf is None:
        try:
            from sector_map import get_parent_etfs
            etfs = get_parent_etfs(ticker)
            sector_etf = etfs[0] if etfs else None
        except Exception:
            sector_etf = None
    return ETF_ARCHETYPE.get(sector_etf, DEFAULT_ARCHETYPE)


# ---------------------------------------------------------------------------
# Per-archetype rubrics — each awards up to 5 points on metrics that fit the model.
# A criterion only scores when its data is present; missing data is never a penalty.
# ---------------------------------------------------------------------------
def _gt(x, t):
    return pd.notna(x) and x is not None and x > t


def _score_software(r):
    s = 0
    s += _gt(r.get("rev_growth_yoy"), 20)
    s += _gt(r.get("gross_margin"), 50)
    s += _gt(r.get("op_margin"), 15)
    s += _gt(r.get("eps_growth"), 10)
    s += _gt(r.get("operating_cf_B"), 0)
    return int(s)


def _score_platform(r):
    s = 0
    s += _gt(r.get("rev_growth_yoy"), 10)            # huge base → lower growth bar
    opm, opm_prev = r.get("op_margin"), r.get("op_margin_prev")
    s += (_gt(opm, 10) or (pd.notna(opm) and pd.notna(opm_prev) and opm > opm_prev))
    s += _gt(r.get("roe"), 15)
    s += _gt(r.get("eps_growth"), 10)
    s += _gt(r.get("operating_cf_B"), 0)
    return int(s)


def _score_financial(r):
    s = 0
    s += _gt(r.get("roe"), 12)
    eff = r.get("efficiency_ratio")
    s += (pd.notna(eff) and eff < 60) if pd.notna(eff) else _gt(r.get("op_margin"), 25)
    s += _gt(r.get("eps_growth"), 5)                 # banks compound slower
    s += _gt(r.get("ttm_net_income"), 0)
    s += (_gt(r.get("rev_growth_yoy"), 3) or _gt(r.get("roe"), 15))
    return int(s)


def _score_energy(r):
    s = 0
    s += _gt(r.get("roe"), 10)
    s += _gt(r.get("operating_cf_B"), 0)             # cash generation, not growth
    dte = r.get("debt_to_equity")
    s += (pd.notna(dte) and dte < 0.5)
    s += _gt(r.get("ttm_net_income"), 0)
    s += _gt(r.get("op_margin"), 10)
    return int(s)


def _score_industrial(r):
    s = 0
    s += _gt(r.get("op_margin"), 10)
    s += _gt(r.get("roe"), 12)
    s += _gt(r.get("eps_growth"), 5)                 # cyclical → lower bar
    s += _gt(r.get("operating_cf_B"), 0)
    s += _gt(r.get("rev_growth_yoy"), 0)             # trough-tolerant: just positive
    return int(s)


def _score_staple(r):
    s = 0
    s += _gt(r.get("roe"), 15)
    s += _gt(r.get("op_margin"), 8)
    s += _gt(r.get("operating_cf_B"), 0)
    s += _gt(r.get("rev_growth_yoy"), 3)
    s += bool(r.get("dividend_payer"))
    return int(s)


def _score_health(r):
    """Healthcare / medical devices / life-sciences tools — quality compounders, not
    hypergrowth SaaS. The franchise hallmarks are durable operating margins, strong
    returns on capital, a steady cash engine (recurring consumables/services), and
    steady — not explosive — top- and bottom-line growth. (gross_margin is
    deliberately NOT used: Polygon often omits gross_profit for these names, e.g. TMO,
    so it would penalize on missing data, not economics.) Pre-profit biotech is caught
    upstream by the pre_profit archetype."""
    s = 0
    s += _gt(r.get("op_margin"), 15)                 # high-margin device/tools/pharma
    s += _gt(r.get("operating_cf_B"), 0)             # recurring cash engine
    s += _gt(r.get("roe"), 12)                       # returns on capital
    s += _gt(r.get("eps_growth"), 8)                 # steady compounding (< SaaS bar)
    s += _gt(r.get("rev_growth_yoy"), 5)             # durable secular growth, not 20%+
    return int(s)


def _score_consumer(r):
    s = 0
    s += _gt(r.get("rev_growth_yoy"), 10)
    s += _gt(r.get("op_margin"), 8)
    s += _gt(r.get("roe"), 15)
    s += _gt(r.get("eps_growth"), 10)
    s += _gt(r.get("operating_cf_B"), 0)
    return int(s)


def _score_pre_profit(r):
    """Pre-profit names can't be judged on earnings — score the path to it. Caps low
    by design; a binary/story stock should not screen as a quality compounder."""
    s = 0
    s += _gt(r.get("rev_growth_yoy"), 40)            # genuine hypergrowth
    s += _gt(r.get("gross_margin"), 50)              # real unit economics
    s += _gt(r.get("operating_cf_B"), 0)             # self-funding
    s += _gt(r.get("op_margin"), -10)                # losses not catastrophic
    s += _gt(r.get("rev_growth_yoy"), 150)           # bonus for explosive growth
    return int(s)


_RUBRICS = {
    "software":   _score_software,
    "platform":   _score_platform,
    "financial":  _score_financial,
    "energy":     _score_energy,
    "industrial": _score_industrial,
    "healthcare": _score_health,
    "staple":     _score_staple,
    "consumer":   _score_consumer,
    "pre_profit": _score_pre_profit,
}


def score_fundamentals(row, archetype=None):
    """0-5 fundamental score using the rubric for the row's business archetype.
    `eps_growth` should be the stable TTM figure (set by the caller)."""
    arch = archetype or row.get("archetype") or DEFAULT_ARCHETYPE
    return _RUBRICS.get(arch, _score_software)(row)
