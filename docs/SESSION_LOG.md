# Session Log — Stock Pipeline Project

For sessions 1-7 see docs/SESSION_ARCHIVE.md

---

## Project state (as of Session 9)

**Environment:** WSL Ubuntu 22.04, conda env `stock` (Python 3.11)
**GitHub:** github.com/spencerwidell/stock-pipeline
**Stack:** Polygon.io API → fetch_stock.py → Parquet → DuckDB → analysis

**Files:**
- `fetch_stock.py` — fetches 15 tickers, 6 years, saves to Parquet
- `vsa_features.py` — direction, spread, rel_spread, rel_volume
- `vsa_labels.py` — classifies bars into 6 VSA types + neutral
- `analyze.py` — DuckDB queries: top closes, avg close, daily returns
- `scripts/morning_startup.sh` — health check + git pull
- `scripts/run_pipeline.sh` — nohup fetch with timestamped logging

**Data:**
- `data/stock_ohlcv.parquet` — 21,920 rows, 15 tickers, 6 years
- `data/stock_vsa.parquet` — same + direction, spread, rel_spread,
  rel_volume, vsa_label

**Tickers:** AMZN, NVDA, MSFT, META, TSLA, ELF, CELH, PLTR, AVGO,
            SOFI, TSM, NOW, IBM, CRM, ORCL

---

## Session 8 — June 6, 2026

**Built:** `vsa_labels.py` — deterministic bar classification
- Added rel_spread to vsa_features.py (spread / 10d rolling mean)
- Thresholds: wide >= 1.5, narrow <= 0.7, high vol >= 1.5, low vol <= 0.7
- 6 label types: buying_climax, selling_climax, effort_up,
  effort_down, no_demand, no_supply + neutral
- 315 bars: 269 neutral, 46 labeled

**First hypothesis test — next-day returns by VSA label (21-day sample):**
- buying_climax: 12 bars, +3.09% avg next-day
- no_supply: 5 bars, -3.16%
- WARNING: sample too small, results were noise

**Concepts:** LEAD() window function, python -c for one-off queries,
rel_spread normalization mirrors rel_volume pattern

---

## Session 9 — June 6, 2026

**Expanded dataset:** 21-day → 6 years (21,920 rows)
- PLTR: 1,427 days (IPO Sep 2020), SOFI: 1,260 days (SPAC Jun 2021)
- META: 1,149 days — needs investigation

**Hypothesis tests with full dataset:**

Next-day returns — all labels cluster 0.10-0.17%, essentially noise.
Small sample findings from Session 8 were statistical noise.

5-day and 10-day returns:
- buying_climax: +3.11% (5d), +4.23% (10d) — strongest signal
- effort_up: +0.34% (5d), +1.91% (10d) — slow developing
- no_demand: weakest at both horizons

Regime analysis — buying_climax by year:
- 2022: +17.20% over 5 days (67 bars) — bear market mean reversion
- 2021/2023/2024: +0.83% to +1.32% — modest in bull markets
- 2025/2026: negative (-0.71%, -1.63%)
- 2022 outlier drives the overall +3.11% average

2022 isolation test — only buying_climax showed +17.20%.
All other labels near zero or negative in 2022.
Signal is regime-conditional, not universal.

**Key finding:** buying_climax is a strong mean reversion signal in
bear markets, weak or negative in bull markets. Next layer needed:
market regime classifier before applying VSA labels.

---

## Session 10 — (upcoming)

- Build market regime classifier (bull/bear/sideways)
- Use 200-day MA or drawdown-based classification
- Re-run VSA hypothesis tests conditioned on regime
- Determine if buying_climax edge is robust within bear regime

---

## Session start checklist
- [ ] Open Ubuntu app
- [ ] `cd ~/projects/stock-pipeline`
- [ ] `./scripts/morning_startup.sh`
- [ ] `conda activate stock`
- [ ] `git status`
