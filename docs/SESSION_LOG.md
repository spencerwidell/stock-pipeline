# Session Log — Stock Pipeline Project

For sessions 1-7 see docs/SESSION_ARCHIVE.md

---

## Project state (as of Session 13)

**Environment:** WSL Ubuntu 22.04, conda env `stock` (Python 3.11)
**GitHub:** github.com/spencerwidell/stock-pipeline
**Stack:** Polygon.io API → fetch_stock.py → Parquet → DuckDB → analysis

**Files:**
- `fetch_stock.py` — fetches 22 tickers, 6 years, saves to Parquet
- `vsa_features.py` — direction, spread, rel_spread, rel_volume,
  ma20/50/200, dist_ma200, ma200_slope, regime, channel_pos
- `vsa_labels.py` — classifies bars into 6 VSA types + neutral
- `widell_line.py` — swing state machine, wl_state, wl_flip
- `analyze.py` — DuckDB queries
- `scripts/morning_startup.sh` — health check + git pull
- `scripts/run_pipeline.sh` — nohup fetch with timestamped logging

**Data:**
- `data/stock_ohlcv.parquet` — 30,962 rows, 21 tickers, 6 years
- `data/stock_vsa.parquet` — full feature set including Widell Line

**Universe:**
- Tech/growth (15): AMZN, NVDA, MSFT, META, TSLA, ELF, CELH,
  PLTR, AVGO, SOFI, TSM, NOW, IBM, CRM, ORCL
- Market (2): SPY, QQQ
- Value/defensive (4): JPM, PG, XOM, GLD
- BRK-B: failed (Polygon symbol issue, investigate later)

**Pipeline order (must run in sequence):**
1. `python vsa_features.py`
2. `python vsa_labels.py`
3. `python widell_line.py`

---

## Session 12 — June 7, 2026

**Combined signal test:** inconclusive + buying_climax + mixed = +11.53%
**Stress test revealed 2022 artifact** — signal negative in all other years
**Key lesson:** Always stress test headline results by year/regime

---

## Session 13 — June 7, 2026

**Expanded universe:** 15 → 21 tickers (added SPY, QQQ, JPM, PG, XOM, GLD)

**buying_climax by segment (5-day return):**
- tech/growth: +3.11% (501 bars)
- value/defensive: +0.73% (86 bars)
- market ETFs: -0.01% (30 bars)

**buying_climax by segment and year:**
- 2022 outlier (+17.20%) is entirely in tech/growth — rate-hike snapbacks
- Value/defensive is MORE CONSISTENT: positive in 5 of 7 years,
  clustering +1.25% to +1.79%, no massive outlier
- Market ETFs: no signal, useful as benchmark

**Key findings:**
- VSA buying_climax is a stock-selection signal, not market-timing
- Tech/growth: high magnitude, regime-dependent, 2022-driven
- Value/defensive: lower magnitude, more consistent across regimes
- Market ETFs confirm: signal doesn't work on broad indices

**Research insight:** Consistency often more valuable than magnitude
in a trading system. Value/defensive buying_climax may be more
practically useful than tech despite lower average return.

---

## Session 14 — (upcoming)

- Test Widell Line states on value/defensive vs tech segments
- Does the up/down/inconclusive separation hold across segments?
- Investigate BRK-B Polygon symbol issue
- Begin thinking about signal scoring: combine regime + wl_state
  + vsa_label + segment into a composite score

---

## Session start checklist
- [ ] Open Ubuntu app
- [ ] `cd ~/projects/stock-pipeline`
- [ ] `./scripts/morning_startup.sh`
- [ ] `conda activate stock`
- [ ] `git status`

---

## Session 14 — June 7, 2026

**Widell Line validation across segments:**

| Segment | Up | Inconclusive | Down | Spread |
|---|---|---|---|---|
| Tech/Growth | +2.38% | +0.95% | -0.83% | 3.21% |
| Value/Defensive | +1.17% | +0.23% | -0.44% | 1.61% |
| Market ETFs | +0.65% | +0.34% | -0.33% | 0.98% |

**Key finding:** Widell Line is a universal framework — up > inconclusive
> down ordering holds across all three segments. Signal strength scales
with volatility. Tech produces the widest spread, market ETFs the narrowest.

**Implication:** Framework is valid as a general tool. Threshold
calibration may need to be segment-specific. A composite score could
weight signals by segment volatility.

---

## Session 15 — (upcoming)

- Build composite signal score combining regime + wl_state + vsa_label
- Weight by segment volatility
- Test composite score forward returns vs individual signals
- Begin thinking about ML feature matrix
