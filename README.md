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

- ✅ Every claim is treated as a hypothesis
- ✅ Every signal is tested across multiple market regimes (2020–2026)
- ✅ All code, data pipelines, and findings are version-controlled
- ✅ Complexity is added only when simpler models fail

---

## 🔬 Key Findings (so far)

### The Widell Line
An original swing-structure state machine built from first principles.
Tracks resistance (swing highs) and support (swing lows) to assign
three states per bar: **up**, **down**, or **inconclusive**.

| State | Bars | 5-Day Return |
|---|---|---|
| 🟢 Up | 3,294 | +2.38% |
| 🟡 Inconclusive | 16,744 | +0.95% |
| 🔴 Down | 1,882 | -0.83% |

Clean separation ordered exactly as theory predicts.

### VSA Bar Classification
Six deterministic bar types derived from relative volume and spread:
buying_climax, selling_climax, effort_up, effort_down, no_demand, no_supply

### Signal is Regime-Conditional
The same signal produces dramatically different results across market regimes:

| Segment | 5-Day Return |
|---|---|
| 🚀 Tech/Growth | +3.11% (regime-dependent) |
| 🏦 Value/Defensive | +0.73% (consistent across regimes) |
| 📊 Market ETFs | -0.01% (no signal) |

### The 2022 Lesson
A combined signal (Widell inconclusive + buying_climax + mixed regime)
showed +11.53% average — but stress-testing revealed it was entirely
driven by 2022 bear market snapback rallies (+58% that year alone).

Lesson: Always stress-test headline results by year and regime.
This is what separates rigorous research from marketing.

---

## 🏗️ Analytical Stack

Layer 1: Deterministic  →  VSA bar labels, Widell Line states
Layer 2: Statistical    →  Hypothesis testing, regime analysis
Layer 3: ML             →  Phase detection, sequence models (upcoming)
Layer 4: LLM            →  Contextual augmentation (upcoming)
Layer 5: Production     →  Backtesting, monitoring (upcoming)

---

## 📁 Project Structure

stock-pipeline/
├── fetch_stock.py           Polygon.io API → Parquet (21 tickers, 6 years)
├── vsa_features.py          OHLCV → VSA features + regime columns
├── vsa_labels.py            Deterministic bar classification
├── widell_line.py           The Widell Line state machine
├── analyze.py               DuckDB analytical queries
├── scripts/
│   ├── morning_startup.sh   Daily health check
│   └── run_pipeline.sh      Automated fetch with nohup logging
├── data/                    Parquet files (gitignored)
│   ├── stock_ohlcv.parquet  Raw OHLCV (30,962 rows)
│   └── stock_vsa.parquet    Full feature set
├── logs/                    Pipeline logs (gitignored)
└── docs/
    ├── SESSION_LOG.md        Current research log
    ├── SESSION_ARCHIVE.md    Historical session archive
    ├── RESEARCH_ROADMAP.md   Vision, findings, session arc
    └── DECISIONS.md          Architectural decisions

---

## 🛠️ Stack

| Tool | Purpose |
|---|---|
| Python 3.11 | Core language |
| Polygon.io API | Market data (6 years, 21 tickers) |
| Apache Parquet | Columnar storage |
| DuckDB | SQL analytics directly on Parquet |
| pandas + pyarrow | Data processing |
| Bash | Automation and pipeline scripts |
| Git + GitHub | Version control |

---

## 🚀 Getting Started

git clone https://github.com/spencerwidell/stock-pipeline.git
cd stock-pipeline
conda create -n stock python=3.11
conda activate stock
pip install requests pandas pyarrow duckdb python-dotenv

echo "POLYGON_API_KEY=your_key_here" > .env

python fetch_stock.py
python vsa_features.py
python vsa_labels.py
python widell_line.py
python analyze.py

---

## 📊 Universe

| Segment | Tickers |
|---|---|
| 🚀 Tech/Growth | AMZN, NVDA, MSFT, META, TSLA, ELF, CELH, PLTR, AVGO, SOFI, TSM, NOW, IBM, CRM, ORCL |
| 📊 Market | SPY, QQQ |
| 🏦 Value/Defensive | JPM, PG, XOM, GLD |

---

## 📖 Research Log

Full session-by-session research log in docs/SESSION_LOG.md
Research vision and roadmap in docs/RESEARCH_ROADMAP.md

---

## 👤 Author

Spencer Widell — Senior Data Scientist
Building toward lead DS role through production engineering and
quantitative research.

This project is part of a structured learning arc covering CLI fluency,
shell automation, production-grade Python, and agentic workflow management.

---

⚠️ Disclaimer: This is a research project, not financial advice.
All findings are empirical observations on historical data.
Past performance does not predict future results.
