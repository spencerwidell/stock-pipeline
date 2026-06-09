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

---

## Session 15 — June 7, 2026

**Built:** `composite_score.py` — additive signal scoring
- score_wl: wl_state mapped to +2/0/-2
- score_flip: flip direction +1/-1/0
- score_vsa: vsa_label mapped to +2 to -2
- score_regime: bull/mixed/bear mapped to +1/0/-1
- composite: sum of all four, range -6 to +6

**Score vs 5-day return:**
- Score 2+: consistently +1.47% to +2.15%
- Score -3 and below: negative to flat
- Middle zone (-1 to +1): noisy, no clear edge

**Score by segment:**
| Segment | High (2+) | Neutral | Low (-3) | Spread |
|---|---|---|---|---|
| Tech/Growth | +2.16% | +0.85% | -0.63% | 2.79% |
| Value/Defensive | +0.99% | +0.20% | -0.18% | 1.17% |
| Market ETFs | +0.49% | +0.33% | +0.21% | 0.28% |

**Key finding:** Composite score is universal — high beats neutral
beats low in every segment. Spread scales with volatility.
Market ETFs insufficient spread to be actionable.

**Layer 2 complete:** Features built in Layer 1 have measurable,
consistent predictive power across segments and regimes.
Green light to begin ML layer.

---

## Session 16 — (upcoming)

- Begin ML layer — feature matrix preparation
- Define target variable: 5-day forward return bucketed into
  up/flat/down classes
- Train first classifier on composite features
- Evaluate whether ML improves on the simple composite score

---

## Session start checklist
- [ ] Open Ubuntu app
- [ ] `cd ~/projects/stock-pipeline`
- [ ] `./scripts/morning_startup.sh`
- [ ] `conda activate stock`
- [ ] `git status`

---

## Session 16 — June 7, 2026

**Built:** `ml_classifier.py` and `ml_feature_test.py`
- RandomForest with TimeSeriesSplit (5 folds)
- MLflow experiment tracking (widell_vsa_classifier, widell_feature_isolation)
- Feature isolation test: MA only, VSA only, Widell only, all features

**Baselines established:**
- Always predict "up": 0.443 (most common class = 44.3% of bars)
- Random baseline: 0.363

**Feature isolation results:**
- All features:  0.362 — at random baseline
- MA only:       0.332 — below random
- Widell only:   0.331 — below random
- VSA only:      0.317 — worst of all

**The VSA chapter is closed.**
No feature set beats naive baseline. VSA labels are the weakest
feature set tested. Adding all features together barely reaches random.

**The gap between DuckDB and ML findings:**
DuckDB showed real average differences (Widell up = +2.38%).
ML cannot classify individual bars reliably because variance is too
high. These signals work as filters that shift average outcomes,
not as classifiers for individual bar prediction. This is a
meaningful distinction for practical use.

**Research pivot confirmed:**
Signals are useful as overlays and filters in a rules-based system.
ML classification of individual bars is not the right application.
The Widell Line + regime framework is the original contribution.
VSA labels are background context, not primary signal.

**Next focus — what IS working:**
- Widell Line state separation is real and consistent
- Regime-conditional signals shift averages meaningfully
- Composite scoring as a filter (score 2+ vs score -3 and below)
- These work as portfolio filters, not trade-by-trade classifiers

---

## Session 17 — (upcoming)

- VSA in sequence — test consecutive label patterns
- Weekly bar aggregation — does weekly VSA improve signal?
- After completion: pivot to Widell Line deeper investigation
- Parameter optimization: does N=5 or N=10 swing window improve
  state separation vs N=3?

---

## Session start checklist
- [ ] Open Ubuntu app
- [ ] `cd ~/projects/stock-pipeline`
- [ ] `./scripts/morning_startup.sh`
- [ ] `conda activate stock`
- [ ] `git status`

---

## Session 17 — June 8, 2026

**VSA sequence test — consecutive labels:**
- buying_climax 2 consecutive: -0.48% (59 bars) — signal reverses
- no_supply 2 consecutive: +0.89% — marginal improvement
- 3-consecutive samples too small to trust (6 bars max)
- Conclusion: consecutive labels don't strengthen VSA signal

**VSA weekly bar test — 4 week forward returns:**
- All labels positive (1.17% to 3.13%)
- No theoretical ordering — effort_down nearly matches effort_up
- Market upward drift swamps all label differences
- Conclusion: weekly VSA shows drift, not signal

**VSA chapter fully closed.**
Tested across: daily next-day, daily 5-10 day, daily consecutive
sequence, weekly 4-week. No consistent standalone predictive signal
found across timeframes or methods.

**The pivot:**
VSA served as scaffolding that led to the Widell Line — which shows
consistent, theoretically ordered signal separation. The original
contribution of this project is the Widell Line framework, not VSA.

---

## Session 18 — (upcoming)

- Widell Line parameter optimization — test N=2, N=5, N=10
  swing window vs current N=3
- Does wider window produce cleaner state separation?
- Test Widell Line on weekly bars
- Begin thinking about practical signal generation system

---

## Session start checklist
- [ ] Open Ubuntu app
- [ ] `cd ~/projects/stock-pipeline`
- [ ] `./scripts/morning_startup.sh`
- [ ] `conda activate stock`
- [ ] `git status`

---

## Session 18 — June 8, 2026

**Built:** New features in vsa_features.py, ml_alpha_test.py

**New features added:**
- close_pos: where in the bar did price close (0=low, 1=high)
- upper_wick, lower_wick: rejection ratios
- effort: rel_spread * rel_volume combined
- roc_20: 20-day rate of change (momentum)
- dist_52w_high, dist_52w_low: distance from 52-week extremes

**Widell Line parameter optimization (widell_optimize.py):**
- Tested N=2,3,5,7,10 swing window
- N=3 confirmed as optimal — spread collapses at N=5
- Original parameter choice empirically validated

**ML alpha target test (SPY-relative outperformance):**
- Switching from raw return to alpha removed market drift
- Naive baseline dropped from 0.443 to 0.368
- Results:
  - widell_only:    0.352 (below naive)
  - new_features:   0.400 (beats naive by +0.032)
  - widell_plus_new: 0.412 (beats naive by +0.044)
  - all_features:   0.410

**First time beating naive baseline.**

**Feature importances:**
- dist_52w_high: 24.9% — dominant predictor
- dist_52w_low:  21.4%
- ma200_slope:   13.2%
- dist_ma200:    12.4%
- roc_20:         8.1%
- vsa_encoded:    0.08% — confirmed irrelevant
- score_vsa:      0.11% — confirmed irrelevant

**Key finding:** 52-week distance features dominate. Stocks near
52-week lows recovering outperform; stocks near highs consolidate.
The Widell Line adds 3-4% importance — modest but real contribution.
VSA labels confirmed irrelevant in ML context.

---

## Session 19 — (upcoming)

- Hyperparameter tuning — max_depth, min_samples_leaf, n_estimators
- Test deeper trees now that we have a signal worth tuning
- Add segment as a feature (tech/value/market encoding)
- Consider adding more tickers to strengthen the training set
- Update RESEARCH_ROADMAP.md with final findings

---

## Session start checklist
- [ ] Open Ubuntu app
- [ ] `cd ~/projects/stock-pipeline`
- [ ] `./scripts/morning_startup.sh`
- [ ] `conda activate stock`
- [ ] `git status`

---

## Session 19 — June 8, 2026

**Built:** ml_xgboost.py, ml_tune.py, ml_optuna.py, tests/test_pipeline.py

**XGBoost vs Random Forest (GPU, alpha target):**
- RandomForest: 0.408
- XGBoost GPU:  0.413 — marginal improvement
- XGBoost feature importances shifted: wl_encoded now #1 at 11.3%
  vs buried in Random Forest. Gradient boosting finds Widell Line
  interactions that Random Forest misses.

**Hyperparameter tuning:**
- Manual grid search: best 0.413 (depth=4, lr=0.05)
- Optuna 50 trials: best 0.417 (depth=4, lr=0.046, n_est=337)
- Marginal gain — likely near ceiling for this feature set/dataset

**GPU enabled:** RTX 4090 confirmed working with XGBoost device=cuda
Each Optuna trial ~7 seconds vs minutes on CPU.

**MLflow UI:** Running at localhost:5000, 5 experiments tracked.
All runs logged with parameters, metrics, and model artifacts.

**Test suite:** 20 pytest tests, all passing in 0.31 seconds.
Covers: data integrity, feature ranges, regime values, VSA labels,
Widell Line state separation, pipeline consistency.

**Key insight:** We are near the ceiling at 0.417 with this feature
set. To improve meaningfully need either:
1. More training data (expand universe further)
2. New feature types (options flow, sentiment, fundamentals)
3. Different model architecture (sequence model for temporal patterns)

---

## Session 20 — (upcoming)

- Update RESEARCH_ROADMAP.md with all ML findings
- Add pytest to morning_startup.sh as a health check
- Add segment encoding as a feature and retest
- Consider sequence model (LSTM or transformer) for temporal patterns
- Begin thinking about production signal generation

---

## Session start checklist
- [ ] Open Ubuntu app
- [ ] `cd ~/projects/stock-pipeline`
- [ ] `./scripts/morning_startup.sh`
- [ ] `conda activate stock`
- [ ] `git status`
- [ ] `pytest tests/ -v`

---

## Session 20 — June 8, 2026

**Built:** ml_lstm.py, sequence features, updated README and DECISIONS

**Sequence features added to composite_score.py:**
- rsi_trend: RSI change over 5 bars
- composite_trend: composite score change over 5 bars
- momentum_5: 5-bar price return
- wl_duration: consecutive bars in current Widell state

**LSTM results:**
- Accuracy: 0.412 — identical to XGBoost
- Sequence model does not outperform gradient boosting
- Daily OHLCV patterns not complex enough to justify LSTM overhead
- XGBoost + engineered sequence features captures same information

**ML ceiling confirmed at ~0.417**
All models cluster 0.408-0.417. Further gains require new data types.

**Documentation updated:**
- README.md: full project overview with all findings
- DECISIONS.md: complete record of all architectural choices

---

## Session 21 — (upcoming)

- Update RESEARCH_ROADMAP.md with final ML findings
- Add pytest to morning_startup.sh health check
- Begin Layer 4 planning: LLM augmentation
- Consider daily signal generation script

---

## Session start checklist
- [ ] Open Ubuntu app
- [ ] `cd ~/projects/stock-pipeline`
- [ ] `./scripts/morning_startup.sh`
- [ ] `conda activate stock`
- [ ] `git status`
- [ ] `pytest tests/ -v`

---

## Session 21 — June 8, 2026

**Built:** run_checks.sh, daily_signals.py, updated RESEARCH_ROADMAP

**run_checks.sh:**
- Runs full pytest suite (20 tests)
- Reports data freshness (latest date, ticker count, row count)
- Run after conda activate stock each morning

**daily_signals.py:**
- Shows current Widell Line state for all 21 tickers
- Includes regime, composite score, RSI, 52w distance, VSA label
- Highlights flips with lightning bolt
- Summary: universe state counts, high/low score counts
- Today's reading: 8 flips, 1 up, 12 inconclusive, 8 down
  QQQ and SPY selling climax — broad market move confirmed

**RESEARCH_ROADMAP.md fully updated:**
- All 8 empirical findings documented
- Widell Line contribution formalized
- Session arc updated through Session 21
- Upcoming sessions: backtesting, universe expansion, LLM

---

## Session 22 — (upcoming)

- Backtesting harness: simulate trading Widell Line flip signals
- Include transaction costs, slippage, position sizing
- Compare: flip-based entry vs composite score filter
- Baseline: buy-and-hold SPY

---

## Session start checklist
- [ ] Open Ubuntu app
- [ ] `cd ~/projects/stock-pipeline`
- [ ] `./scripts/morning_startup.sh`
- [ ] `conda activate stock`
- [ ] `./scripts/run_checks.sh`
- [ ] `git status`

---

## Session 22 — June 8, 2026

**Built:** backtest.py, backtest_v2.py, backtest_v3.py, sector_map.py
Fixed META data corruption (FB/META ticker stitch)

**META data fix:**
Polygon's META ticker contained wrong historical prices (~$15 vs ~$340).
Root cause: different company previously traded as META.
Fix: fetch FB (pre Oct 2021) + META (post Oct 2021), stitch together.
First close now correctly $236.73 in June 2020.

**Backtest V3 — apples to apples (same 15 names):**
System avg: 241.4% vs Buy-and-hold avg: 222.2%
System wins by +19.2% including NVDA/AVGO generational outliers.

**Excluding NVDA and AVGO (generational AI plays):**
System avg: 202.3% vs Buy-and-hold avg: 107.9%
System edge: +94.4 percentage points
System beats BAH: 9/13 names

**Key insight — system value varies by stock type:**
- Volatile growth (PLTR, ELF, CELH, META): system adds significant value
- Steady compounders (MSFT, ORCL, IBM, TSM): BAH wins, system times poorly
- Losers/turnarounds (SOFI, CRM): system protects by reducing exposure
- Generational trends (NVDA, AVGO): just hold, don't time

**Portfolio framework:**
- High conviction secular trends: hold, use system only for breakdown alerts
- Volatile growth names: use Widell Line for entry timing and sizing
- Value/turnaround plays: system entry signals add real value

**Top-down filter added:** sector_map.py maps each stock to its
parent sector ETF and broad market ETF for top-down confirmation.

---

## Session 23 — (upcoming)

- Position sizing backtest: full/half/zero based on Widell state
- Add gap + volume feature (daily open vs prev close)
- Friday close signal test
- Begin thinking about alert system for signal changes

---

## Session start checklist
- [ ] Open Ubuntu app
- [ ] `cd ~/projects/stock-pipeline`
- [ ] `./scripts/morning_startup.sh`
- [ ] `conda activate stock`
- [ ] `./scripts/run_checks.sh`
- [ ] `git status`
