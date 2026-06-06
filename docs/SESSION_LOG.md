# Session Log — Stock Pipeline Project

For sessions 1-7 see docs/SESSION_ARCHIVE.md

---

## Project state (as of Session 10)

**Environment:** WSL Ubuntu 22.04, conda env `stock` (Python 3.11)
**GitHub:** github.com/spencerwidell/stock-pipeline
**Stack:** Polygon.io API → fetch_stock.py → Parquet → DuckDB → analysis

**Files:**
- `fetch_stock.py` — fetches 15 tickers, 6 years, saves to Parquet
- `vsa_features.py` — direction, spread, rel_spread, rel_volume,
  ma20/50/200, dist_ma200, ma200_slope, regime, channel_pos
- `vsa_labels.py` — classifies bars into 6 VSA types + neutral
- `analyze.py` — DuckDB queries: top closes, avg close, daily returns
- `scripts/morning_startup.sh` — health check + git pull
- `scripts/run_pipeline.sh` — nohup fetch with timestamped logging

**Data:**
- `data/stock_ohlcv.parquet` — 21,920 rows, 15 tickers, 6 years
- `data/stock_vsa.parquet` — full feature set including regime columns

**Schema highlights:**
- `regime` — bull/bear/mixed based on MA20/50/200 stack alignment
- `dist_ma200` — % distance from 200MA (+ above, - below)
- `ma200_slope` — rate of change of 200MA over 10 bars
- `channel_pos` — standard deviations from 20MA (Bollinger position)

---

## Session 9 — June 6, 2026

**Expanded dataset:** 21-day → 6 years (21,920 rows)

**Key finding:** buying_climax is regime-conditional
- 2022 (bear): +17.20% over 5 days — strong mean reversion
- 2021/2023/2024 (bull): +0.83% to +1.32% — weak
- 2025/2026: negative
- Next-day returns: all labels 0.10-0.17%, noise

---

## Session 10 — June 6, 2026

**Built:** Regime feature set in vsa_features.py
- MA20, MA50, MA200 per ticker (rolling per group)
- dist_ma200: % distance from 200MA
- ma200_slope: rate of change over 10 bars
- regime: bull/bear/mixed based on full MA stack alignment
- channel_pos: Bollinger-style position within 20MA band

**Key finding — buying_climax conditioned on regime:**
- bear regime: -0.35% over 5 days (83 bars) — avoid
- bull regime: +1.13% over 5 days (219 bars) — modest
- mixed regime: +6.72% over 5 days (199 bars) — strong signal

**Interpretation:** The signal lives in regime transitions, not
confirmed trends. Mixed regime = MA stack not fully aligned =
market in transition. Buying climax in a transition zone catches
exhaustion at potential turning points. This validates the core
insight behind the Larsson Line (inconclusive zone matters)
derived empirically from our own data.

The 2022 finding from Session 9 is now explained — 2022 had
elevated mixed regime bars as the market transitioned bull→bear
and back. It was transition zone signal, not bear market signal.

---

## Session 11 — (upcoming)

- Build Larsson-style state machine using swing highs/lows
  (LAG/LEAD window functions)
- Three states: up (above resistance), down (below support),
  inconclusive (between lines)
- Detect flips — state transitions bar to bar
- Test flip signal forward returns vs regime classifier
- Compare: does Larsson state outperform MA stack regime?

---

## Session start checklist
- [ ] Open Ubuntu app
- [ ] `cd ~/projects/stock-pipeline`
- [ ] `./scripts/morning_startup.sh`
- [ ] `conda activate stock`
- [ ] `git status`
