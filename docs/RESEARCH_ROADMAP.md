# Stock Pipeline Research Roadmap

## Project Vision

This is a production-grade research platform built from first principles, not a portfolio project. The goal is to empirically test whether Volume Spread Analysis and Wyckoff principles contain predictive signal, and if so, to quantify that signal in a way that can be used systematically.

Most market analysis frameworks are built on tradition and intuition rather than empirical validation. This project challenges that by treating every claim as a hypothesis to be tested. We start with the simplest deterministic rules, measure their behavior across real data, and build complexity only when simpler models fail.

The infrastructure is designed to support serious research: versioned data, reproducible pipelines, SQL-first analysis for transparency, and clean separation between data acquisition, feature engineering, and modeling.

## The Analytical Stack

The research progresses through five distinct layers, each building on the foundation of the previous:

### Layer 1: Deterministic / Rule-Based
**What it is:** Direct boolean logic applied to raw OHLCV data. If volume > average AND spread < threshold, classify as accumulation.

**What belongs here:** VSA bar classifications, support/resistance level detection, trend rules, higher highs/lower lows swing structure, moving average regime filters, pattern matching expressible as SQL window functions.

**Why it comes first:** Deterministic rules are transparent, debuggable, and produce the same result every time. They force you to articulate exactly what you mean by "accumulation" or "strength" before adding statistical complexity. If a deterministic rule has no signal, a probabilistic version won't magically create one.

### Layer 2: Statistical / Probabilistic
**What it is:** Measuring distributions, correlations, and statistical significance of the patterns detected in Layer 1. Does "no demand" actually correlate with price decline? How strong is that correlation? Is it ticker-specific or universal?

**What belongs here:** Hypothesis testing on VSA classifications, volume distribution analysis, correlation studies between bar types and future returns, regime-conditioned signal testing.

**Why it comes after Layer 1:** You need the deterministic features first. This layer answers "do these rules actually mean anything?" before you invest in complex models.

### Layer 3: Machine Learning
**What it is:** Pattern recognition over sequences of VSA features, phase detection, multi-factor models that combine dozens of signals.

**What belongs here:** Sequence models for Wyckoff phase transitions, feature importance analysis, ensemble methods over VSA+price structure, anomaly detection.

**Why it comes after Layer 2:** If the statistical layer shows no correlation between your features and outcomes, ML will just overfit noise. ML excels at finding complex interactions between features that already have marginal predictive power.

### Layer 4: LLM Augmentation
**What it is:** Using language models to contextualize numerical patterns with news, sentiment, or earnings transcripts.

**What belongs here:** News-to-feature extraction, sentiment scoring, fundamental data ingestion, contextual pattern explanation.

**Why it comes after Layer 3:** LLMs add context to signals that already work. They don't create signals from scratch.

### Layer 5: Production Infrastructure
**What it is:** Real-time ingestion, backtesting harness, monitoring, alerting, portfolio construction, risk management.

**Why it comes last:** Infrastructure supports a validated research finding. Building production systems before you have a working model is premature optimization.

## The Wyckoff Foundation

The project uses Wyckoff/VSA as the analytical framework, but with a specific progression:

**Start with VSA (Volume Spread Analysis):** Individual bar classification based on volume, spread, and close position. Each bar gets a deterministic label: No Demand, Climactic Action, Test, etc.

**Progress to Classic Wyckoff:** Phase detection (Accumulation, Markup, Distribution, Markdown) requires sequence modeling across multiple bars. This belongs in Layer 3 because it's sequential pattern recognition.

**Why start with VSA:** Bar-by-bar features are SQL-friendly, deterministic, and provide the inputs for phase detection later. You can't detect accumulation phases until you can reliably detect individual accumulation bars.

## Empirical Findings (updated as research progresses)

### Finding 1 — VSA labels do not predict next-day returns (Sessions 8-9)
With 21,920 rows across 6 years, all VSA labels produce next-day returns of 0.10-0.17% — indistinguishable from the market's natural upward drift. Next-day is too short a horizon for VSA patterns to play out.

### Finding 2 — VSA labels show weak signal at 5-10 day horizons (Session 9)
At 5 days, buying_climax leads at +3.11% and effort_up at +0.34%.
At 10 days, buying_climax +4.23%, effort_up +1.91%.
However this average is heavily distorted by 2022.

### Finding 3 — buying_climax is regime-conditional (Session 9)
By year:
- 2022 (bear): +17.20% over 5 days — strong mean reversion signal
- 2021/2023/2024 (bull): +0.83% to +1.32% — weak
- 2025/2026 (current): -0.71% to -1.63% — negative

In 2022, buying_climax was the ONLY label with strong positive returns.
All other labels were near zero or negative that year.

**Interpretation:** buying_climax marks exhaustion points in bear market
selloffs. Short-term traders buy the dip, price snaps back 5-10 days,
then the bear trend resumes. This is mean reversion, not trend reversal.
The signal is not universal — it requires regime classification first.

### Finding 4 — classical VSA theory partially contradicted (Session 9)
Theory says climax bars = bearish (distribution). Data shows climax bars
produce positive forward returns in most regimes. However no_supply and
no_demand behave as theory predicts (weakest forward returns).

## Feature Roadmap (Layer 1 expansion)

Based on Sessions 8-9 findings, the following features are planned before
moving to statistical modeling:

### Regime Classification (Session 10)
- 200-day MA: price above = bull, below = bear (simplest, most tested)
- MA stack: 20/50/200 alignment for trend strength and momentum
- Higher highs / lower lows: swing structure using LAG() window functions
  — price-action based regime, no indicator lag

### Momentum Features (Session 11)
- Rate of change: (close - close_Nd) / close_Nd for N = 5, 10, 20, 50 days
- MA crossovers: 20/50, 50/200 — classic momentum signals
- Distance from 52-week high/low — measures trend exhaustion

### Price Structure Features (Session 12)
- Higher highs / lower lows sequence length — how many consecutive bars
  confirm the current trend structure
- Swing high/low detection using rolling window comparisons
- Support/resistance proximity

### Volume Profile (Session 13)
- Institutional proxy: abnormally large volume bars relative to time of day
  (requires intraday data — check Polygon minute aggregates)
- Volume trend: is volume expanding or contracting within a trend

### Universe Expansion (Session 14)
Add to the current 15 tech/growth tickers:
- SPY, QQQ — market regime ground truth
- JPM, BRK.B, PG — value/defensive names for cross-regime comparison
- XOM, GLD — commodities proxy, different cycle behavior
Rationale: current universe is highly correlated tech/growth stocks.
All findings may be tech-bull-regime artifacts. Diverse universe
tests generalizability.

## Open Research Questions

### Regime Questions (now the priority)
- Does buying_climax edge persist within confirmed bear regimes, or
  is 2022 a one-year anomaly?
- What regime classifier best separates the signal? 200MA, swing
  structure, or drawdown-based?
- Do VSA thresholds (1.5x volume, 1.5x spread) need regime-specific
  calibration?

### Signal Structure Questions
- Does combining regime + VSA label produce a stronger signal than
  either alone?
- What is the optimal forward window for each label type?
- Do signals strengthen on weekly bars where noise is filtered out?

### Universe Questions
- Are findings tech-sector artifacts or universal VSA signals?
- Do value stocks (JPM, BRK.B) show different VSA signal structure
  than growth stocks?
- Does signal strength correlate with liquidity or market cap?

### Practical Implementation
- What is the false positive rate of each VSA classification within
  a confirmed regime?
- Can multiple weak signals (regime + VSA + momentum) combine into
  a tradeable edge?
- What position sizing and stop-loss logic is implied by the
  mean-reversion character of the buying_climax signal?

## The Session Arc (revised)

### Completed
- Sessions 1-3: Infrastructure — WSL, conda, Git, GitHub, Parquet pipeline
- Sessions 4-5: Shell automation — morning_startup.sh, run_pipeline.sh
- Session 6: DuckDB — SQL queries directly on Parquet
- Sessions 7-8: VSA features and bar classification
- Session 9: Dataset expansion (6 years), multi-horizon hypothesis testing,
  regime analysis — buying_climax regime-conditional finding

### Planned
- Session 10: Regime classifier — 200MA bull/bear, re-run VSA tests
  conditioned on regime
- Session 11: Higher highs/lower lows swing structure, MA stack (20/50/200)
- Session 12: Momentum features — rate of change, MA crossovers,
  distance from 52-week high/low
- Session 13: Universe expansion — add SPY, QQQ, value and commodity names
- Session 14: Re-run all hypothesis tests on expanded universe,
  test for tech-sector bias
- Session 15: First ML layer — regime-conditioned signal combination
- Session 16: Wyckoff phase detection as sequence classification problem
- Session 17+: LLM augmentation, production infrastructure

## Guiding Principles

### 1. Learn from First Principles
Don't accept Wyckoff or VSA as gospel. Treat every claim as a hypothesis. "Accumulation is characterized by high volume and narrow spread" is a testable proposition, not an axiom.

### 2. Deterministic Before Probabilistic
If you can't write a deterministic rule that shows even weak signal, a probabilistic model won't save you. Start with the simplest possible logic.

### 3. Interpretable Before Complex
A 10-factor linear model that you can explain beats a 100-feature neural network that you can't. Interpretability is not a luxury; it's required for iterating on hypotheses.

### 4. Infrastructure Before Analysis
SQL pipelines, versioned data, and reproducible queries are not "nice to have." They're prerequisites for trusting your results.

### 5. Test Everything Empirically
Intuition and market folklore are starting points, not conclusions. Every claim must survive contact with real data before it earns a place in the model.

### 6. Regime First
No signal should be evaluated without regime context. A signal that works in bear markets and fails in bull markets is not a broken signal — it is a regime-conditional signal. Know which regime you are in before applying any rule.

---

**Note:** This roadmap is a living document. Empirical findings section updates
every session. Session arc updates when plans change based on what we learn.
