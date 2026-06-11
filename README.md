# 📈 Stock Pipeline — Empirical Market Structure Research → Live Signal System

A quantitative research platform built from first principles that has graduated
into a **live, automated daily signal system**. It began by empirically testing
whether **Volume Spread Analysis (VSA)** and **Wyckoff principles** contain
predictive signal; that research produced the **Widell Line** — an original
swing-structure state machine — which now drives a deployed pipeline that scores
a 99-ticker universe every day and pushes actionable, plain-English signals to a
dashboard and to Telegram.

> *"Most market analysis frameworks are built on tradition and intuition.
> This project challenges that by treating every claim as a hypothesis
> to be tested — then ships only what survives the test into production."*

**Where it stands today:** the research layers (deterministic → statistical →
ML) are complete, and the project is now a production decision-support product.
A daily pipeline computes Widell Line states, composite and conviction scores,
fundamentals, moat ratings, valuation (PE/PEG/P-OCF), and top-down sector
rotation; an **intelligence layer** adds an LLM plain-English daily briefing
(Claude), a **secular-theme engine** (coverage / gaps / concentration), and
**macro + bond-market (TLT) regime** context. It's surfaced through a six-tab
Streamlit dashboard on AWS and **three** daily Telegram alerts (morning, close,
narrative briefing). Goals and risk controls are documented in
`docs/KEY_OBJECTIVES.md` and `docs/MODEL_RISK.md`.

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
Layer 4: LLM            - Plain-English narrative briefing + quarterly moat
                          scoring (Claude) - Live
Layer 5: Production     - Daily pipeline, composite + conviction scoring,
                          fundamentals, valuation, sector rotation, dashboard,
                          three Telegram alerts - Live
Layer 6: Intelligence   - Secular-theme engine, macro/bond (TLT) regime,
                          exit/trim framework, portfolio coverage - Live

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
| Moat rating | 1 to 5 | Durability of the competitive advantage (Claude, quarterly) |
| Valuation | PE / PEG / P-OCF | Price paid — *context, not part of conviction* |
| Sector rotation | 23 ETFs ranked | Which sector to be in, then which laggard within it |
| Theme coverage | 11 secular themes | Which trends you own, gaps, and over-concentration |
| Bond regime (TLT) | tailwind / headwind / neutral | Is the macro backdrop for growth supportive? |

Composite and conviction are intentionally separate axes: composite says which
way the signal points, conviction says whether it's a quality entry *right now*.
Moat, valuation, and themes are quality/context layers — they inform the briefing
and dashboard but do **not** alter the conviction score.

**Delivery:**
- **Streamlit dashboard** on AWS EC2 (`http://18.188.180.99:8501`) — six tabs:
  Briefing (the LLM read), Themes (secular coverage + TLT regime), Signals (with a
  High Conviction callout), Fundamentals (F score + moat + valuation), Guide, and
  Rotation.
- **Telegram alerts**, three on weekdays via cron:
  - **10:30 AM ET — morning alert** (`morning_alert.py`): live Polygon snapshot
    prices vs yesterday's levels — high-conviction entries, breakout watch, notable
    moves, 💼 position check, and theme opportunities. No pipeline re-run.
  - **4:30 PM ET — close alert** (`telegram_alert.py`): full pipeline recompute +
    signal summary with conviction scores.
  - **4:30 PM ET — narrative briefing** (`narrative_alert.py`): a plain-English
    Claude briefing (market context, actionable setups, watch list, portfolio
    check, bottom line) — the interpretation layer over the raw signals.

---

## 📁 Project Structure

stock-pipeline/
├── Data pipeline
│   ├── fetch_stock.py        Polygon.io API to Parquet (99 tickers, 6 years)
│   ├── fetch_fundamentals.py Quarterly financials → F score (0-5) + valuation inputs
│   ├── fetch_earnings.py     Forward earnings dates (yfinance) → 🗓️ flag
│   ├── vsa_features.py       OHLCV to VSA features + regime + RSI/MACD + channel
│   ├── vsa_labels.py         Deterministic bar classification
│   ├── widell_line.py        The Widell Line state machine (N=3)
│   ├── composite_score.py    Additive signal scoring (-6 to +6)
│   ├── conviction_score.py   Buy-zone quality scoring (0-10)
│   └── moat_score.py         Quarterly competitive-moat rating via Claude (1-5)
├── Intelligence layer
│   ├── narrative_alert.py    LLM plain-English daily briefing (Claude) + persistence
│   ├── valuation.py          PE / PEG / P-OCF from price + TTM inputs (context)
│   ├── positions.py          Exit/trim status for held names (TRIM/REVIEW/HOLD)
│   ├── theme_engine.py       Secular-theme overlay: coverage, gaps, TLT regime
│   └── macro_calendar.py     CPI/FOMC proximity → narrative macro context
├── Config (single sources of truth)
│   ├── universe.yaml         Tracked universe + sector mapping (manage_universe.py)
│   ├── universe.py           Loader/writer for universe.yaml
│   ├── manage_universe.py    CLI: --add / --remove / --list tickers
│   ├── holdings.yaml         Current positions + weights + CASH (dry powder)
│   ├── themes.yaml           Human-curated secular-trend map (11 themes)
│   └── macro_calendar.yaml   Hand-maintained CPI/FOMC dates
├── Top-down / delivery
│   ├── sector_map.py         Ticker → sector/broad ETF mapping (reads universe.yaml)
│   ├── sector_rotation.py    Sector ranking + constituent laggard scanner (CLI)
│   ├── daily_signals.py      Console signal summary
│   ├── dashboard.py          Streamlit dashboard (Briefing/Themes/Signals/Fund/Guide/Rotation)
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
├── data/                 Parquet/JSON files (gitignored — regenerate on deploy)
│   ├── stock_ohlcv.parquet     Raw OHLCV
│   ├── stock_vsa.parquet       Full feature + signal set
│   ├── fundamentals.parquet    F score + valuation inputs
│   ├── earnings.parquet        Forward earnings dates
│   ├── moat.parquet            Quarterly moat ratings
│   └── narrative_latest.json   Last LLM briefing (shown in the dashboard)
├── logs/                 Pipeline logs (gitignored)
└── docs/
    ├── KEY_OBJECTIVES.md    What the system is for and its non-goals
    ├── MODEL_RISK.md        Model-risk register + monitoring
    ├── SESSION_LOG.md       Current research/build log
    ├── SESSION_ARCHIVE.md   Historical session archive
    ├── RESEARCH_ROADMAP.md  Vision, findings, session arc
    └── DECISIONS.md         Architectural decisions

**Automation (AWS EC2 crontab):**
- `30 14 * * 1-5` → morning alert (10:30 AM ET)
- `30 21 * * 1-5` → full daily pipeline + close alert + narrative briefing (4:30 PM ET)

---

## 🛠️ Stack

| Tool | Purpose |
|---|---|
| Python 3.11 | Core language |
| Polygon.io API | Market data (6 years, 99 tickers) + live snapshot prices |
| yfinance | Forward earnings dates |
| Anthropic Claude API | LLM narrative briefing (Sonnet) + moat scoring (Opus) |
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
pip install requests pandas pyarrow duckdb streamlit scikit-learn xgboost optuna mlflow torch pytest anthropic yfinance pyyaml

echo "POLYGON_API_KEY=your_key_here" >> .env
echo "ANTHROPIC_API_KEY=your_key_here" >> .env    # for narrative briefing + moat scoring
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

99 tickers across full GICS sector coverage plus thematic baskets — built to
support top-down sector rotation and secular-theme analysis, not just single-name
signals. Includes **TLT** (20yr Treasury — a bond-market regime signal, not a
position) and **MP** (rare earths). Managed via `manage_universe.py` →
`universe.yaml`.

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

Key objectives & non-goals in docs/KEY_OBJECTIVES.md
Model-risk register & monitoring in docs/MODEL_RISK.md
Full session-by-session build log in docs/SESSION_LOG.md
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
