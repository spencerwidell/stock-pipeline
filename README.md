# 📈 Stock Pipeline — Empirical VSA & Wyckoff Research Platform

A production-grade quantitative research platform built from first principles.
This project empirically tests whether **Volume Spread Analysis (VSA)** and
**Wyckoff principles** contain predictive signal — and quantifies that signal
across multiple market regimes.

> *"Most market analysis frameworks are built on tradition and intuition.
> This project challenges that by treating every claim as a hypothesis
> to be tested."*

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
Layer 5: Production     - Signal generation, backtesting (upcoming)

---

## 📁 Project Structure

stock-pipeline/
├── fetch_stock.py        Polygon.io API to Parquet (21 tickers, 6 years)
├── vsa_features.py       OHLCV to VSA features + regime + RSI/MACD
├── vsa_labels.py         Deterministic bar classification
├── widell_line.py        The Widell Line state machine (N=3)
├── composite_score.py    Additive signal scoring (-6 to +6)
├── widell_optimize.py    N parameter optimization (N=3 confirmed)
├── ml_classifier.py      Random Forest baseline
├── ml_feature_test.py    Feature set isolation tests
├── ml_alpha_test.py      SPY-relative alpha target tests
├── ml_xgboost.py         XGBoost GPU comparison
├── ml_tune.py            Manual hyperparameter grid
├── ml_optuna.py          Bayesian optimization (50 trials)
├── ml_lstm.py            LSTM sequence model
├── analyze.py            DuckDB analytical queries
├── scripts/
│   ├── morning_startup.sh   Daily health check
│   └── run_pipeline.sh      Automated fetch with nohup logging
├── tests/
│   └── test_pipeline.py     20 pytest tests, all passing
├── data/                 Parquet files (gitignored)
│   ├── stock_ohlcv.parquet  Raw OHLCV (30,962 rows)
│   └── stock_vsa.parquet    Full feature set (27 columns)
├── logs/                 Pipeline logs (gitignored)
└── docs/
    ├── SESSION_LOG.md       Current research log
    ├── SESSION_ARCHIVE.md   Historical session archive
    ├── RESEARCH_ROADMAP.md  Vision, findings, session arc
    └── DECISIONS.md         Architectural decisions

---

## 🛠️ Stack

| Tool | Purpose |
|---|---|
| Python 3.11 | Core language |
| Polygon.io API | Market data (6 years, 21 tickers) |
| Apache Parquet | Columnar storage |
| DuckDB | SQL analytics directly on Parquet |
| pandas + pyarrow | Data processing |
| scikit-learn | Random Forest, TimeSeriesSplit |
| XGBoost | Gradient boosting (GPU via CUDA) |
| PyTorch | LSTM sequence model (RTX 4090) |
| Optuna | Bayesian hyperparameter optimization |
| MLflow | Experiment tracking (localhost:5000) |
| pytest | 20-test pipeline validation suite |
| Bash | Automation and pipeline scripts |
| Git + GitHub | Version control |

---

## 🚀 Getting Started

git clone https://github.com/spencerwidell/stock-pipeline.git
cd stock-pipeline
conda create -n stock python=3.11
conda activate stock
pip install requests pandas pyarrow duckdb scikit-learn xgboost optuna mlflow torch pytest

echo "POLYGON_API_KEY=your_key_here" > .env

python fetch_stock.py
python vsa_features.py
python vsa_labels.py
python widell_line.py
python composite_score.py

pytest tests/ -v

python analyze.py
python ml_xgboost.py
python ml_optuna.py

---

## 📊 Universe

| Segment | Tickers |
|---|---|
| Tech/Growth | AMZN, NVDA, MSFT, META, TSLA, ELF, CELH, PLTR, AVGO, SOFI, TSM, NOW, IBM, CRM, ORCL |
| Market | SPY, QQQ |
| Value/Defensive | JPM, PG, XOM, GLD |

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
