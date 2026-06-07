# Session Log — Stock Pipeline Project

For sessions 1-7 see docs/SESSION_ARCHIVE.md

---

## Project state (as of Session 12)

**Environment:** WSL Ubuntu 22.04, conda env `stock` (Python 3.11)
**GitHub:** github.com/spencerwidell/stock-pipeline
**Stack:** Polygon.io API → fetch_stock.py → Parquet → DuckDB → analysis

**Files:**
- `fetch_stock.py` — fetches 15 tickers, 6 years, saves to Parquet
- `vsa_features.py` — direction, spread, rel_spread, rel_volume,
  ma20/50/200, dist_ma200, ma200_slope, regime, channel_pos
- `vsa_labels.py` — classifies bars into 6 VSA types + neutral
- `widell_line.py` — swing state machine, wl_state, wl_flip
- `analyze.py` — DuckDB queries
- `scripts/morning_startup.sh` — health check + git pull
- `scripts/run_pipeline.sh` — nohup fetch with timestamped logging

**Data:**
- `data/stock_ohlcv.parquet` — 21,920 rows, 15 tickers, 6 years
- `data/stock_vsa.parquet` — full feature set including Widell Line

**Pipeline order (must run in sequence):**
1. `python vsa_features.py`
2. `python vsa_labels.py`
3. `python widell_line.py`

---

## Session 11 — June 6, 2026

**Built:** `widell_line.py` — the Widell Line state machine
- Three states: up (+2.38%), inconclusive (+0.95%), down (-0.83%)
- Clean separation ordered exactly as theory predicts
- Flip into up (+1.84%) weaker than established up (+2.56%)

---

## Session 12 — June 7, 2026

**Combined signal test:** Widell inconclusive + buying_climax + mixed regime

Headline: +11.53% over 5 days across 104 bars — appeared strong.

**Stress test by year revealed it's a 2022 artifact:**
- 2020: +0.67% (6 bars)
- 2021: -0.25% (14 bars)
- 2022: +58.05% (22 bars) ← drives the entire average
- 2023: -1.26% (13 bars)
- 2024: -2.71% (14 bars)
- 2025: -0.38% (29 bars)
- 2026: -4.87% (6 bars)

**Key lesson:** Backtests can be completely dominated by a single
regime year. The +11.53% headline was a 2022 bear market artifact,
not a robust edge. Commercial systems that show headline returns
without regime breakdown are hiding this risk.

**What remains valid:**
- The signal may be real specifically in bear markets
- 2022's +58% on 22 bars is not noise — it's a bear market pattern
- The question is whether 2022 is repeatable or a once-per-decade event
- Need more bear market data to answer this (2000-2002, 2008-2009
  would be the test — requires broader historical data)

**Research integrity finding:** The discipline to stress-test the
headline result is what separates rigorous research from marketing.
This is the core value of the empirical approach.

---

## Session 13 — (upcoming)

- Expand universe to include SPY, QQQ — market regime ground truth
- Add value/defensive names (JPM, BRK.B, PG) for cross-regime testing
- Test whether combined signal holds on non-tech names
- Investigate whether 2022 bear market pattern is sector-specific
- Consider pulling longer history (2018-2019) for more bear data

---

## Session start checklist
- [ ] Open Ubuntu app
- [ ] `cd ~/projects/stock-pipeline`
- [ ] `./scripts/morning_startup.sh`
- [ ] `conda activate stock`
- [ ] `git status`
