# Stock Pipeline Research Roadmap

## Project Vision

This is a production-grade research platform built from first principles,
not a portfolio project. The goal is to empirically test whether Volume
Spread Analysis and Wyckoff principles contain predictive signal, and if
so, to quantify that signal in a way that can be used systematically.

Most market analysis frameworks are built on tradition and intuition rather
than empirical validation. This project challenges that by treating every
claim as a hypothesis to be tested. We start with the simplest deterministic
rules, measure their behavior across real data, and build complexity only
when simpler models fail.

## The Analytical Stack

### Layer 1: Deterministic / Rule-Based — COMPLETE
VSA bar classifications, Widell Line state machine, regime features,
composite scoring. All implemented and validated.

### Layer 2: Statistical / Probabilistic — COMPLETE
Hypothesis testing across daily (1d, 5d, 10d), weekly, and consecutive
sequence timeframes. Regime-conditioned analysis. Segment comparison.
All findings documented below.

### Layer 3: Machine Learning — COMPLETE
Random Forest, XGBoost GPU, Optuna tuning, LSTM sequence model.
Best accuracy: 0.417 (XGBoost + Optuna, SPY-relative alpha target).
Ceiling reached with current feature set and universe size.

### Layer 4: LLM Augmentation — UPCOMING
News-to-feature extraction, sentiment scoring, earnings transcript
analysis. Will augment signals that already work, not create new ones.

### Layer 5: Production Infrastructure — UPCOMING
Daily signal generation (daily_signals.py started), backtesting harness,
monitoring, alerting, position sizing, execution simulation.

---

## Empirical Findings

### Finding 1 — VSA labels do not predict returns (Sessions 7-17)
Tested across daily next-day, daily 5-10 day, consecutive sequences,
and weekly bars. No consistent standalone predictive signal found.
VSA labels rank last in ML feature importance (0.08%).
VSA served as theoretical scaffolding that led to the Widell Line.
**VSA chapter closed.**

### Finding 2 — The Widell Line shows consistent state separation (Session 11)
Original swing-structure state machine. N=3 confirmed optimal via
widell_optimize.py. Three states validated across all segments:

| State | Bars | 5-Day Return |
|---|---|---|
| up | 5,031 | +2.38% |
| inconclusive | 23,333 | +0.95% |
| down | 2,598 | -0.83% |

Spread scales with volatility: tech 3.21%, value 1.61%, market 0.98%.
Universal framework — ordering holds across all three segments.

### Finding 3 — Signal is regime-conditional (Sessions 9-10)
buying_climax by year: 2022 bear market +17.20%, 2023-2026 flat/negative.
MA stack regime (bull/mixed/bear) conditions the signal significantly.
Mixed regime buying_climax: +6.72% over 5 days — strongest combination.
But stress-test revealed 2022 dominates; signal inconsistent across years.

### Finding 4 — Flip into up weaker than established up (Session 11)
- Established up state: +2.56%
- Flip into up: +1.84%
Fresh breakouts sometimes fail before continuing. The flip is the
signal moment but established state is the stronger predictor.

### Finding 5 — Composite score works at extremes (Session 15)
Score ≥2: consistently +1.47% to +2.16% across segments.
Score ≤-3: negative to flat on tech, weak on value.
Middle zone (-1 to +1): noisy, no edge.
Works as a filter, not a trade-by-trade classifier.

### Finding 6 — 52-week distance dominates ML features (Session 18)
dist_52w_high: 24.9%, dist_52w_low: 21.4% in XGBoost importance.
This is the well-known 52-week high effect (George & Hwang, 2004).
The Widell Line adds incremental value on top: wl_encoded 11.1%,
score_wl 10.5% — ranks 1st and 2nd among non-momentum features.

### Finding 7 — ML ceiling at 0.417 with current data (Sessions 16-20)
All models cluster 0.408-0.417 on SPY-relative alpha target.
Naive baseline: 0.368. Random baseline: 0.333.
LSTM (0.412) does not outperform XGBoost (0.417).
Sequence model overhead not justified for daily OHLCV features.
Further gains require new data types or broader universe.

### Finding 8 — Value/defensive more consistent than tech (Session 13)
buying_climax value/defensive: positive in 5 of 7 years, no outlier.
buying_climax tech/growth: dominated by 2022 (+17.20%).
Consistency often more valuable than magnitude in a trading system.

---

## The Widell Line — Original Contribution

The Widell Line is an empirically validated swing-structure state machine:

1. Detects swing highs (resistance) and swing lows (support) using
   a confirmed-optimal N=3 bar window each side
2. Forward-fills resistance and support lines
3. Assigns state: up (above resistance), down (below support),
   inconclusive (between lines)
4. Detects flips — state changes bar to bar

Key properties validated empirically:
- N=3 optimal: spread collapses at N=5 (down state goes positive)
- Universal: up > inconclusive > down in all three market segments
- Regime-aware: combined with MA stack produces actionable filters
- Top ML feature: ranks #1 and #2 in XGBoost importance

Named after Spencer Widell. Built from first principles, validated
against 6 years of daily data across 21 tickers and 3 segments.
Compared against and found to outperform classical VSA labels.

---

## Research Mission

The goal is not to replicate existing systems but to empirically
validate, challenge, and improve on them.

Commercial systems like the Larsson Line (support/resistance state
machine) and Wyckoff/VSA frameworks are built on intuition and
selectively backtested. They sell signals without showing the work.

This project does the opposite:
- Every claim is treated as a hypothesis
- Every signal tested across multiple market regimes
- All code, data, and findings version-controlled and public
- Complexity added only when simpler models fail

The Larsson Line benchmark: our empirical version (Widell Line)
produces clean state separation (3.21% spread on tech) validated
across 6 years. The mixed/inconclusive regime insight — that
transition zones matter — was derived from data, not purchased.

---

## Universe Design

Current (21 tickers):
- Tech/growth (15): AMZN, NVDA, MSFT, META, TSLA, ELF, CELH,
  PLTR, AVGO, SOFI, TSM, NOW, IBM, CRM, ORCL
- Market (2): SPY, QQQ
- Value/defensive (4): JPM, PG, XOM, GLD

Expansion path:
- Phase 2: QQQ constituents (~115 tickers) — validate signal on
  liquid institutionally-traded names
- Phase 3: SPY constituents (~500 tickers) — test generalizability
- Phase 4: Full factor grid — sector, style, cap size diversity

Universe expansion driven by ML training data quality, not portfolio
construction. Tech names are phase-correlated — diverse universe
ensures all Wyckoff phases represented in training data.

---

## Session Arc

### Completed
- Sessions 1-3: Infrastructure — WSL, conda, Git, Parquet pipeline
- Sessions 4-5: Shell automation — morning_startup.sh, run_pipeline.sh
- Session 6: DuckDB — SQL directly on Parquet
- Sessions 7-8: VSA features and bar classification
- Session 9: Dataset expansion (6 years), hypothesis testing
- Session 10: Regime classifier — MA stack, channel position
- Session 11: Widell Line — swing state machine, N=3 validated
- Session 12: Combined signal test — 2022 artifact lesson
- Session 13: Universe expansion — value/defensive/market added
- Session 14: Widell Line validated across all segments
- Session 15: Composite signal scoring (-6 to +6)
- Session 16: ML baseline — Random Forest, feature isolation
- Session 17: VSA sequence and weekly tests — chapter closed
- Session 18: New features (RSI, MACD, 52w distance), alpha target
- Session 19: XGBoost GPU, Optuna, pytest suite
- Session 20: LSTM — no improvement over XGBoost, ceiling confirmed
- Session 21: run_checks.sh, daily_signals.py, roadmap updated

### Upcoming
- Session 22: Backtesting harness — simulate trading the Widell
  Line flip signals with realistic transaction costs
- Session 23: Universe expansion to QQQ constituents
- Session 24: LLM augmentation — earnings sentiment as feature
- Session 25+: Production pipeline, monitoring, alerting

---

## Guiding Principles

1. **Learn from First Principles** — treat every claim as a hypothesis
2. **Deterministic Before Probabilistic** — simple rules first
3. **Interpretable Before Complex** — explainability is required
4. **Infrastructure Before Analysis** — reproducibility is prerequisite
5. **Test Everything Empirically** — intuition is a starting point
6. **Regime First** — no signal evaluated without regime context
7. **Stress Test Headlines** — year-by-year breakdown is mandatory

---

*This roadmap is a living document. Updated through Session 21.*
