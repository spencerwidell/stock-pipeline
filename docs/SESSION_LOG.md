# Session Log — Stock Pipeline Project

For sessions 1-6 see docs/SESSION_ARCHIVE.md

---

## Project state (as of Session 7)

**Environment:** WSL Ubuntu 22.04, conda env `stock` (Python 3.11)
**GitHub:** github.com/spencerwidell/stock-pipeline
**Stack:** Polygon.io API → fetch_stock.py → Parquet → DuckDB → analysis

**Files:**
- `fetch_stock.py` — fetches 15 tickers, 30 days, saves to Parquet
- `vsa_features.py` — adds direction, spread, rel_volume columns
- `analyze.py` — DuckDB queries: top closes, avg close, daily returns
- `scripts/morning_startup.sh` — health check + git pull
- `scripts/run_pipeline.sh` — nohup fetch with timestamped logging

**Data:**
- `data/stock_ohlcv.parquet` — 315 rows, 15 tickers, ~21 trading days
- `data/stock_vsa.parquet` — same + direction, spread, rel_volume

**Tickers:** AMZN, NVDA, MSFT, META, TSLA, ELF, CELH, PLTR, AVGO,
            SOFI, TSM, NOW, IBM, CRM, ORCL

---

## Session 7 — June 6, 2026

**Built:** `vsa_features.py` — first analytical layer
- `direction` (up/down), `spread` (high-low), `rel_volume` (vol/10d ma)
- Saved to `data/stock_vsa.parquet`

**Key findings from DuckDB query (rel_volume > 1.5):**
- IBM May 21: 3.18x volume, up bar — strongest signal, matches 8.77% daily return
- May 29 cluster: IBM, ORCL, PLTR, MSFT all high volume same day
- SOFI May 29: high volume, $0.91 spread — effort with no result

**Concepts:** groupby().transform() for per-ticker rolling calc,
wide spread + high volume = significant VSA bar,
high volume + narrow spread = supply absorbing demand

---

## Session 8 — (upcoming)

- Add named VSA bar labels (~6 types: up thrust, selling climax,
  no demand, no supply, etc.)
- First statistical queries: do high-volume up bars continue or reverse?
- Begin hypothesis-testing layer

---

## Session start checklist
- [ ] Open Ubuntu app
- [ ] `cd ~/projects/stock-pipeline`
- [ ] `./scripts/morning_startup.sh`
- [ ] `conda activate stock`
- [ ] `git status`
