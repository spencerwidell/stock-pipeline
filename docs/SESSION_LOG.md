# Session Log — Stock Pipeline Project

For sessions 1-7 see docs/SESSION_ARCHIVE.md

---

## Project state (as of Session 11)

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

## Session 10 — June 6, 2026

**Built:** Regime feature set in vsa_features.py
- MA20, MA50, MA200, dist_ma200, ma200_slope, regime, channel_pos

**Key finding — buying_climax conditioned on MA regime:**
- bear: -0.35%, bull: +1.13%, mixed: +6.72% over 5 days
- Signal lives in regime transitions, not confirmed trends
- Validates the Larsson Line inconclusive zone insight empirically

---

## Session 11 — June 6, 2026

**Built:** `widell_line.py` — the Widell Line state machine
- Swing high/low detection using N=3 bar window each side
- Forward-fills resistance (swing highs) and support (swing lows)
- Three states: up (above resistance), down (below support),
  inconclusive (between lines)
- wl_flip: True when state changes from previous bar
- Named after Spencer Widell — original empirical framework

**Key findings — Widell Line forward returns (5-day):**
- up state: +2.38% (3,294 bars)
- inconclusive: +0.95% (16,744 bars)
- down state: -0.83% (1,882 bars)
- Clean separation, ordered exactly as theory predicts

**Flip analysis:**
- Flip into up: +1.84% — weaker than established up (+2.56%)
  Fresh breakouts sometimes fail before continuing
- Flip into inconclusive from down: -0.52% vs established down -0.99%
  Losing the down state improves forward returns significantly
- Flip into inconclusive: +1.30% vs established inconclusive +0.91%

**Next test (Session 12):** Combine Widell Line state + VSA
buying_climax in mixed regime — does the combination produce
stronger signal than either alone?

---

## Session 12 — (upcoming)

- Test combined signal: Widell Line flip to inconclusive +
  VSA buying_climax in mixed MA regime
- Add momentum features: rate of change (5, 10, 20, 50 day)
- Add MA crossover signals (20/50, 50/200)
- Begin thinking about signal combination scoring

---

## Session start checklist
- [ ] Open Ubuntu app
- [ ] `cd ~/projects/stock-pipeline`
- [ ] `./scripts/morning_startup.sh`
- [ ] `conda activate stock`
- [ ] `git status`
