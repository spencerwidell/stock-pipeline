# 📈 Stock Pipeline — Empirical Market Structure Research → Live Signal System

A quantitative research platform built from first principles that has graduated
into a **live, automated daily signal system**. It began by empirically testing
whether **Volume Spread Analysis (VSA)** and **Wyckoff principles** contain
predictive signal; that research produced the **Widell Line** — an original
swing-structure state machine — which now drives a deployed pipeline that scores
a 97-ticker universe every day and pushes actionable signals to a dashboard and
to Telegram.

> *"Most market analysis frameworks are built on tradition and intuition.
> This project challenges that by treating every claim as a hypothesis
> to be tested — then ships only what survives the test into production."*

**Where it stands today:** the research layers (deterministic → statistical →
ML) are complete and documented, and the project is now in its production phase —
a daily pipeline computes Widell Line states, composite and conviction scores,
fundamentals, and top-down sector rotation, surfaced through a Streamlit
dashboard on AWS and twice-daily Telegram alerts.

---

## 🎯 Research Mission

Commercial trading systems sell signals without showing the work.
This project does the opposite:

- Every claim is treated as a hypothesis
- Every signal is tested across multiple market regimes (2020-2026)
- All code, data pipelines, and findings are version-controlled
- Complexity is added only when simpler models fail

---

## 🔬 Key Findings

### The Widell Line
An original swing-structure state machine built from first principles.
Tracks resistance (swing highs) and support (swing lows) using a
confirmed-optimal N=3 bar window to assign three states per bar:
up, down, or inconclusive.

| State | Bars | 5-Day Return |
|---|---|---|
| Up | 5,031 | +2.38% |
| Inconclusive | 23,333 | +0.95% |
| Down | 2,598 | -0.83% |

Clean separation validated across tech/growth, value/defensive,
and market ETF segments. Named after Spencer Widell.

### VSA Bar Classification - Chapter Closed
Six deterministic bar types tested across daily (1d, 5d, 10d),
consecutive sequence, and weekly timeframes. No consistent
standalone predictive signal found. VSA labels rank last in
ML feature importance (0.08%). VSA served as the theoretical
scaffolding that led to the Widell Line.

### Signal is Regime-Conditional

| Segment | Widell Up | Widell Down | Spread |
|---|---|---|---|
| Tech/Growth | +2.38% | -0.83% | 3.21% |
| Value/Defensive | +1.17% | -0.44% | 1.61% |
| Market ETFs | +0.65% | -0.33% | 0.98% |

### ML Layer Results
Using SPY-relative alpha as target (removes market drift):

| Model | Accuracy | vs Naive (0.368) |
|---|---|---|
| Random Forest | 0.408 | +0.040 |
| XGBoost GPU | 0.413 | +0.045 |
| XGBoost + Optuna | 0.417 | +0.049 |
| LSTM GPU | 0.412 | +0.044 |

Top ML features: dist_52w_high (24.9%), dist_52w_low (21.4%),
wl_encoded (11.1%), score_wl (10.5%) - the Widell Line ranks
1st and 2nd among non-momentum features.

### The 2022 Lesson
A combined signal showed +11.53% average - but stress-testing
revealed it was entirely driven by 2022 bear market snapbacks.
Always stress-test headline results by year and regime.

---

## 🏗️ Analytical Stack

Layer 1: Deterministic  - VSA bar labels, Widell Line - Complete
Layer 2: Statistical    - Hypothesis testing, regime analysis - Complete
Layer 3: ML             - XGBoost 0.417, LSTM 0.412 - Complete
Layer 4: LLM            - Contextual augmentation (upcoming)
Layer 5: Production     - Daily pipeline, composite + conviction scoring,
                          sector rotation, dashboard, Telegram alerts - Live

---

## 🛰️ Production Signal System

The research has shipped. A daily pipeline turns the Widell Line and supporting
features into signals delivered through two surfaces — a dashboard to explore
and Telegram to push.

**Synthesis layers (computed each run, stored in `stock_vsa.parquet`):**

| Signal | Range | What it answers |
|---|---|---|
| Widell Line state | up / inconclusive / down | Where is price vs swing structure? |
| Composite score | -6 to +6 | Momentum / signal *direction* |
| Conviction score | 0 to 10 | Entry *quality* — channel position + fundamentals + state + flip recency |
| Fundamental score | 0 to 5 | Quality of the underlying business |
| Sector rotation | 23 ETFs ranked | Which sector to be in, then which laggard within it |

Composite and conviction are intentionally separate axes: composite says which
way the signal points, conviction says whether it's a quality entry *right now*.

**Delivery:**
- **Streamlit dashboard** on AWS EC2 (`http://18.188.180.99:8501`) — four tabs:
  Signals (with a High Conviction callout), Fundamentals, Guide, and Rotation.
- **Telegram alerts**, twice daily on weekdays via cron:
  - **10:30 AM ET — morning alert** (`morning_alert.py`): live Polygon snapshot
    prices measured against yesterday's computed levels. High-conviction names in
    entry range, breakout watch, and notable open moves. No pipeline re-run.
  - **4:30 PM ET — close alert** (`telegram_alert.py`): full pipeline recompute
    + signal summary with conviction scores.

---

## 📁 Project Structure

stock-pipeline/
├── Data pipeline
│   ├── fetch_stock.py        Polygon.io API to Parquet (97 tickers, 6 years)
│   ├── fetch_fundamentals.py Quarterly financials → fundamental score (0-5)
│   ├── vsa_features.py       OHLCV to VSA features + regime + RSI/MACD + channel
│   ├── vsa_labels.py         Deterministic bar classification
│   ├── widell_line.py        The Widell Line state machine (N=3)
│   ├── composite_score.py    Additive signal scoring (-6 to +6)
│   └── conviction_score.py   Buy-zone quality scoring (0-10)
├── Top-down / delivery
│   ├── sector_map.py         Ticker → sector/broad ETF mapping + constituents
│   ├── sector_rotation.py    Sector ranking + constituent laggard scanner (CLI)
│   ├── daily_signals.py      Console signal summary
│   ├── dashboard.py          Streamlit dashboard (Signals/Fundamentals/Guide/Rotation)
│   ├── telegram_alert.py     Close alert — full signal push
│   └── morning_alert.py      Morning alert — live snapshot vs yesterday's levels
├── Research / ML
│   ├── widell_optimize.py    N parameter optimization (N=3 confirmed)
│   ├── ml_classifier.py      Random Forest baseline
│   ├── ml_xgboost.py         XGBoost GPU comparison
│   ├── ml_optuna.py          Bayesian optimization (50 trials)
│   ├── ml_lstm.py            LSTM sequence model
│   └── analyze.py            DuckDB analytical queries
├── scripts/
│   ├── run_daily.sh          Production pipeline (fetch→features→score→alert)
│   ├── run_morning_alert.sh  Morning alert wrapper (portable conda activation)
│   └── morning_startup.sh    Local daily health check
├── tests/
│   └── test_pipeline.py      20 pytest tests, all passing
├── data/                 Parquet files (gitignored)
│   ├── stock_ohlcv.parquet   Raw OHLCV
│   ├── stock_vsa.parquet     Full feature + signal set
│   └── fundamentals.parquet  Per-ticker fundamental scores
├── logs/                 Pipeline logs (gitignored)
└── docs/
    ├── SESSION_LOG.md       Current research log
    ├── SESSION_ARCHIVE.md   Historical session archive
    ├── RESEARCH_ROADMAP.md  Vision, findings, session arc
    └── DECISIONS.md         Architectural decisions

**Automation (AWS EC2 crontab):**
- `30 14 * * 1-5` → morning alert (10:30 AM ET)
- `30 21 * * 1-5` → full daily pipeline + close alert (4:30 PM ET)

---

## 🛠️ Stack

| Tool | Purpose |
|---|---|
| Python 3.11 | Core language |
| Polygon.io API | Market data (6 years, 97 tickers) + live snapshot prices |
| Apache Parquet | Columnar storage |
| DuckDB | SQL analytics directly on Parquet |
| pandas + pyarrow | Data processing |
| Streamlit | Interactive dashboard (deployed on AWS EC2) |
| Telegram Bot API | Push alerts (morning + close) |
| scikit-learn | Random Forest, TimeSeriesSplit |
| XGBoost | Gradient boosting (GPU via CUDA) |
| PyTorch | LSTM sequence model (RTX 4090) |
| Optuna | Bayesian hyperparameter optimization |
| MLflow | Experiment tracking (localhost:5000) |
| pytest | 20-test pipeline validation suite |
| AWS EC2 + cron | Production hosting + twice-daily automation |
| Bash | Automation and pipeline scripts |
| Git + GitHub | Version control |

---

## 🚀 Getting Started

git clone https://github.com/spencerwidell/stock-pipeline.git
cd stock-pipeline
conda create -n stock python=3.11
conda activate stock
pip install requests pandas pyarrow duckdb streamlit scikit-learn xgboost optuna mlflow torch pytest

echo "POLYGON_API_KEY=your_key_here" >> .env
echo "TELEGRAM_TOKEN=your_bot_token" >> .env      # optional, for alerts
echo "TELEGRAM_CHAT_ID=your_chat_id" >> .env      # optional, for alerts

# Run the full daily pipeline (fetch → features → scores → signals)
bash scripts/run_daily.sh

# ...or step through it manually:
python fetch_stock.py
python fetch_fundamentals.py
python vsa_features.py
python vsa_labels.py
python widell_line.py
python composite_score.py
python conviction_score.py

pytest tests/ -v

# Explore signals
python daily_signals.py          # console summary
python sector_rotation.py        # top-down sector + laggard scan
streamlit run dashboard.py       # interactive dashboard (port 8501)

# Research / ML
python analyze.py
python ml_xgboost.py
python ml_optuna.py

---

## 📊 Universe

97 tickers across full GICS sector coverage plus thematic baskets — built to
support top-down sector rotation, not just single-name signals.

| Segment | Examples |
|---|---|
| Semiconductors (SMH) | NVDA, AVGO, TSM, AMD, AMAT, LRCX, ASML, ARM |
| Software / security (IGV) | MSFT, CRM, NOW, ORCL, PANW, CRWD, PLTR, SNOW |
| Comm / consumer tech (XLC, XLY) | AAPL, GOOG, META, NFLX, AMZN, COST, TSLA |
| Industrials / infra (XLI, PAVE, GRID) | CAT, GEV, PWR, VRT |
| Aerospace / space / quantum (ITA) | RTX, AXON, RKLB, ASTS, IONQ, RGTI |
| Energy / uranium (XLE, URA) | XOM, CVX, FANG, CCJ, CEG, SMR |
| Financials (XLF) | JPM, SOFI, HOOD, MSTR |
| Sector & broad ETFs | SPY, QQQ, IWM, XLK, XLV, XLP, XLB, XLF, GLD, EEM, + more |

Full mapping in `sector_map.py` (23 sector/thematic ETFs ranked in rotation).

---

## 📖 Research Log

Full session-by-session research log in docs/SESSION_LOG.md
Research vision and roadmap in docs/RESEARCH_ROADMAP.md
Architectural decisions in docs/DECISIONS.md

---

## 👤 Author

Spencer Widell - Senior Data Scientist
Building toward lead DS role through production engineering and
quantitative research. Creator of the Widell Line - an original
empirical swing-structure framework validated across 6 years and
3 market segments.

This project is part of a structured learning arc covering CLI
fluency, shell automation, production-grade Python, ML engineering,
and agentic workflow management.

---

Disclaimer: This is a research project, not financial advice.
All findings are empirical observations on historical data.
Past performance does not predict future results.
