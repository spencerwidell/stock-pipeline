# Stock Pipeline Research Roadmap

## Project Vision

This is a production-grade research platform built from first principles, not a portfolio project. The goal is to empirically test whether Volume Spread Analysis and Wyckoff principles contain predictive signal, and if so, to quantify that signal in a way that can be used systematically.

Most market analysis frameworks are built on tradition and intuition rather than empirical validation. This project challenges that by treating every claim as a hypothesis to be tested. We start with the simplest deterministic rules, measure their behavior across real data, and build complexity only when simpler models fail.

The infrastructure is designed to support serious research: versioned data, reproducible pipelines, SQL-first analysis for transparency, and clean separation between data acquisition, feature engineering, and modeling.

## The Analytical Stack

The research progresses through five distinct layers, each building on the foundation of the previous:

### Layer 1: Deterministic / Rule-Based
**What it is:** Direct boolean logic applied to raw OHLCV data. If volume > average AND spread < threshold, classify as accumulation.

**What belongs here:** VSA bar classifications, support/resistance level detection, trend rules, pattern matching that can be expressed as SQL window functions.

**Why it comes first:** Deterministic rules are transparent, debuggable, and produce the same result every time. They force you to articulate exactly what you mean by "accumulation" or "strength" before adding statistical complexity. If a deterministic rule has no signal, a probabilistic version won't magically create one.

### Layer 2: Statistical / Probabilistic
**What it is:** Measuring distributions, correlations, and statistical significance of the patterns detected in Layer 1. Does "no demand" actually correlate with price decline? How strong is that correlation? Is it ticker-specific or universal?

**What belongs here:** Hypothesis testing on VSA classifications, volume distribution analysis, correlation studies between bar types and future returns, regime detection based on statistical properties.

**Why it comes after Layer 1:** You need the deterministic features first. This layer answers "do these rules actually mean anything?" before you invest in complex models.

### Layer 3: Machine Learning
**What it is:** Pattern recognition over sequences of VSA features, phase detection, multi-factor models that combine dozens of signals.

**What belongs here:** Sequence models for Wyckoff phase transitions, feature importance analysis, ensemble methods over VSA+price structure, anomaly detection.

**Why it comes after Layer 2:** If the statistical layer shows no correlation between your features and outcomes, ML will just overfit noise. ML excels at finding complex interactions between features that already have marginal predictive power.

### Layer 4: LLM Augmentation
**What it is:** Using language models to contextualize numerical patterns with news, sentiment, or earnings transcripts. "This accumulation phase coincided with activist investor announcement."

**What belongs here:** News-to-feature extraction, sentiment scoring, fundamental data ingestion, contextual pattern explanation.

**Why it comes after Layer 3:** LLMs add context to signals that already work. They don't create signals from scratch. Start with price/volume, prove it works, then augment with fundamental/textual data.

### Layer 5: Production Infrastructure
**What it is:** Real-time ingestion, backtesting harness, monitoring, alerting, portfolio construction, risk management.

**What belongs here:** Streaming data pipelines, signal generation in production, position sizing, execution simulation, performance tracking.

**Why it comes last:** Infrastructure supports a validated research finding. Building production systems before you have a working model is premature optimization.

## The Wyckoff Foundation

The project uses Wyckoff/VSA as the analytical framework, but with a specific progression:

**Start with VSA (Volume Spread Analysis):** Individual bar classification based on volume, spread, and close position. Each bar gets a deterministic label: No Demand, Climactic Action, Test, etc. These features are computable directly from OHLCV using SQL window functions, which makes them transparent and auditable.

**Progress to Classic Wyckoff:** Phase detection (Accumulation, Markup, Distribution, Markdown) requires sequence modeling across multiple bars. A "Spring" is not one bar, it's a pattern: support test → volume spike → reversal. This belongs in Layer 3 (ML) because it's sequential pattern recognition.

**Why start with VSA:** Bar-by-bar features are SQL-friendly, deterministic, and provide the inputs for phase detection later. You can't detect accumulation phases until you can reliably detect individual accumulation bars.

The progression mirrors the analytical stack: deterministic bar rules → statistical validation → sequence patterns → context augmentation.

## Universe Design

The universe is designed in phases, expanding deliberately as the research matures:

Phase 1 (Sessions 9-11): Current 15 tickers + QQQ constituents (~115 total). Validate VSA signal exists on liquid, institutionally-traded names where Wyckoff's Composite Man theory should apply most strongly.

Phase 2 (Sessions 12-13): Expand to full SPY constituents (~500 tickers). Test whether signals generalize beyond technology. Compare signal strength by sector.

Phase 3 (Sessions 14+): Add IWM small-cap sample and IWD value factor slice. Full factor grid coverage: large/mid/small × value/growth × sector.

The universe expands in phases rather than all at once for a specific reason: if VSA doesn't work on the most liquid names in the market, it won't work in noisier environments. Prove signal first, then test generalizability.

The ETF-based stratified design covers the full Wyckoff phase space for ML training. Tech names tend to be phase-correlated — when NVDA is in Markup, MSFT likely is too. A diverse universe ensures all four Wyckoff phases (Accumulation, Markup, Distribution, Markdown) are represented in the training data at any given time, because different sectors and styles cycle at different rates. Value stocks may be accumulating while tech is distributing. Small-caps may be in Markdown while large-cap growth is in Markup. This natural phase staggering across the universe is not a portfolio construction consideration — it is a machine learning data quality requirement. A classifier trained only on a single-sector universe will learn that sector's phase timing, not the universal characteristics of the phases themselves.

Every ticker in the universe will carry metadata labels for sector, industry, market cap tier, style (value/growth/blend), and index membership. This enables signal analysis to be sliced by any dimension and supports the core research question: are VSA signals universal or do they require segment-specific thresholds?

Known limitation: any historical universe based on current index membership has survivorship bias — companies that failed or were acquired are absent. Point-in-time index membership data is the correct long-term solution. This is noted as a future improvement.

## Open Research Questions

These are the genuinely unanswered questions we plan to test empirically:

### Volume Signature Questions
- **Do accumulation and distribution have distinct volume signatures in practice?** Wyckoff theory says yes, but across what percentage of observations? Is the signal clear or marginal?
- **What relative volume threshold separates "normal" from "climactic"?** Is it 2x average? 3x? Does it vary by ticker or market regime?
- **Does "effort vs result" (large volume, small spread = absorption) predict future price movement?** What's the forward window—1 day, 5 days, 20 days?

### Signal Universality Questions
- **Are VSA patterns ticker-specific or universal?** Does a "No Demand" bar mean the same thing for AAPL as for a penny stock?
- **Do signal thresholds vary by volatility regime?** Is 2x volume "climactic" in both high-VIX and low-VIX environments?
- **Do these patterns degrade in higher timeframes (weekly, monthly)?** Or do they strengthen because noise is filtered out?

### Wyckoff's Laws
- **Can we quantify the "Cause and Effect" law?** If accumulation (cause) spans X bars with Y volume, does markup (effect) have predictable magnitude?
- **What constitutes "confirmation" of a phase transition?** How many consecutive signals before you trust a Spring or Upthrust?

### Practical Implementation
- **What's the false positive rate of each VSA classification?** If you flag 100 "No Demand" bars, how many precede actual declines?
- **Can you combine multiple weak signals into a strong one?** Does No Demand + proximity to resistance + downtrend improve prediction?

### Universe and Training Data Questions
- **Does phase diversity in the training universe meaningfully improve Wyckoff phase classifier performance vs a single-sector universe?**
- **Do VSA signal thresholds require segment-specific calibration (tech vs value, large vs small) or are universal thresholds sufficient?**
- **What is the minimum observations-per-phase required for a reliable classifier? How many tickers and what time window achieves that?**

These questions are not rhetorical. They're the research agenda. Every session builds tools to answer one or more of them.

## The Session Arc

This is the planned progression through the research stack:

- **Session 4-5:** Bash automation — morning_startup.sh, run_pipeline.sh, set -euo pipefail
- **Session 6:** DuckDB — SQL queries directly on Parquet files
- **Session 7:** Expand universe to S&P 500 or custom watchlist
- **Session 8:** Cron scheduling — automated daily pipeline, data quality checks
- **Session 9:** VSA feature engineering in SQL — spread, relative volume, close position
- **Session 10:** Deterministic bar classification — No Demand, Climactic Action, Test patterns
- **Session 11:** Signal backtesting framework — forward returns by signal type
- **Session 12:** Volume profile analysis — volume at price, value areas
- **Session 13:** Wyckoff phase detection — accumulation/distribution schematics
- **Session 14:** First ML layer — propensity model on VSA features
- **Session 15:** LLM integration — Claude as research assistant on DuckDB data
- **Session 16+:** Open research questions, custom framework development

Each session outputs:
1. **Code/SQL** that implements the capability
2. **Analysis** that answers at least one research question
3. **Documentation** that explains what was learned and what remains open

## Guiding Principles

### 1. Learn from First Principles
Don't accept Wyckoff or VSA as gospel. Treat every claim as a hypothesis. "Accumulation is characterized by high volume and narrow spread" is a testable proposition, not an axiom.

### 2. Deterministic Before Probabilistic
If you can't write a deterministic rule that shows even weak signal, a probabilistic model won't save you. Start with the simplest possible logic.

### 3. Interpretable Before Complex
A 10-factor linear model that you can explain beats a 100-feature neural network that you can't. Interpretability is not a luxury; it's required for iterating on hypotheses.

### 4. Infrastructure Before Analysis
SQL pipelines, versioned data, and reproducible queries are not "nice to have." They're prerequisites for trusting your results. Don't analyze data you can't reproduce.

### 5. Test Everything Empirically
Intuition and market folklore are starting points, not conclusions. Every claim must survive contact with real data before it earns a place in the model.

### 6. Build for Production, Research in Stages
The infrastructure should be production-grade from day one (proper schemas, error handling, monitoring). The analytical models progress from simple to complex as evidence accumulates.

---

**Note:** This roadmap is a living document. As research progresses and new questions emerge, sections should be updated to reflect our evolving understanding. The session arc may reorder or expand based on what we learn at each stage.
