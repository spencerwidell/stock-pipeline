# 📈 Stock Pipeline — A Personal Investing Intelligence System

**A personal investing intelligence system for the concentrated, conviction-driven
long-term investor.**

> *Empirical rigor earned the foundations. The system now exists to turn those
> foundations into clear, honest, plain-English decisions for a specific investing
> philosophy: wide moats, secular trends toward the future, cash-flowing now, held
> in a concentrated portfolio of 10 best-in-class names.*

---

## What it does today

Every weekday the system scores a 99-ticker universe and answers one question in
plain English: **"What, if anything, should I do today?"**

- **Daily narrative briefing** — an LLM (Claude) reads the entire signal stack and
  writes a plain-English brief: market context, actionable setups, watch list,
  portfolio check, and a one-line bottom line. Delivered to Telegram after the close
  and shown in the dashboard.
- **Secular theme map** — every name is mapped to a multi-year trend (AI infra/
  software, power & grid, reindustrialization, defense, critical materials, …). The
  system shows which themes you cover, where the **gaps** are, where you're
  **over-concentrated**, and the best entry in each.
- **Conviction scoring (0–10)** — entry quality right now: channel position +
  fundamentals + Widell state + flip recency. ≥8 = highest priority.
- **Quality + valuation context** — fundamental score (0–5), moat rating (1–5), and
  valuation (PE / PEG / P-OCF) frame whether a business is durable and reasonably
  priced — context, never an auto-buy.
- **Macro awareness** — the bond-market (TLT) regime and the CPI/FOMC calendar frame
  whether it's an environment to act or wait. The system can't see news, so it says
  so and treats flips around macro events as likely noise.
- **Position management** — flags held names that are extended (trim) or breaking
  down (review). No hard stops — long-term framing.

The full mission and non-goals live in **[docs/KEY_OBJECTIVES.md](docs/KEY_OBJECTIVES.md)**;
known risks and controls in **[docs/MODEL_RISK.md](docs/MODEL_RISK.md)**.

## Who it's for

One investor, with a specific philosophy that the whole system is designed around:

- Holds **~10 (max 10–15) best-in-class single names** — no index/ETF positions.
- Wants the **single best company in each secular trend**, not the basket.
- Ideal company: **wide moat × future-facing secular trend × cash-flowing now.**
- Uses signals for **entry timing and position validation, not trading.**
- Intellectually honest about valuation and timing risk; willing to wait.

## Architecture overview

Four layers, each feeding the next, ending in a plain-English decision:

```
1. Signal stack      Widell Line state · composite score · regression channel
   (where is price?)  → direction and swing structure

2. Quality stack     fundamental score · moat rating · valuation (PE/PEG/P-OCF)
   (is it worth it?)  → durable business at a sane price?

3. Theme layer       themes.yaml → coverage · gaps · concentration · best entry
   (does it fit?)     → a deliberate set of secular bets, not an accumulation

4. Narrative         Claude reads 1-3 + holdings + macro/bond regime + earnings
   intelligence       → "what should I do today?" in plain English
   (so what?)
```

Conviction is the spine (entry quality); the quality, theme, and macro layers are
context that the narrative weaves together. **The system advises; the human decides
— it never places a trade.**

---

## 🛰️ Production Signal System

**Synthesis layers (computed each run, stored in `stock_vsa.parquet` + sidecars):**

| Signal | Range | What it answers |
|---|---|---|
| Widell Line state | up / inconclusive / down | Where is price vs swing structure? |
| Composite score | -6 to +6 | Momentum / signal *direction* |
| Conviction score | 0 to 10 | Entry *quality* — channel + fundamentals + state + flip recency |
| Fundamental score | 0 to 5 | Quality of the underlying business |
| Moat rating | 1 to 5 | Durability of the competitive advantage (Claude, quarterly) |
| Valuation | PE / PEG / P-OCF | Price paid — *context, not part of conviction* |
| Theme coverage | 11 secular themes | Which trends you own, gaps, over-concentration |
| Bond regime (TLT) | tailwind / headwind / neutral | Is the macro backdrop for growth supportive? |
| Sector rotation | 23 ETFs ranked | Which sector to be in, then which laggard within it |

Moat, valuation, and themes inform the briefing and dashboard but do **not** alter
the conviction score — conviction stays a clean buy-zone-quality metric.

**Delivery:**
- **Streamlit dashboard** on AWS EC2 (`http://18.188.180.99:8501`) — six tabs:
  Briefing (the LLM read), Themes (secular coverage + TLT regime), Signals (with a
  High Conviction callout), Fundamentals (F score + moat + valuation), Guide
  (objectives + model-risk docs in-app), and Rotation.
- **Telegram alerts**, three on weekdays via cron:
  - **10:30 AM ET — morning alert** (`morning_alert.py`): live snapshot prices vs
    yesterday's levels — entries in range, breakout watch, notable moves, position
    check, theme opportunities. No pipeline re-run.
  - **4:30 PM ET — close alert** (`telegram_alert.py`): full recompute + signal summary.
  - **4:30 PM ET — narrative briefing** (`narrative_alert.py`): the plain-English
    Claude interpretation over the raw signals.

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
├── Validated foundations (research / ML — see "How It Was Built")
│   ├── widell_optimize.py    N parameter optimization (N=3 confirmed)
│   ├── ml_classifier.py      Random Forest baseline
│   ├── ml_xgboost.py         XGBoost GPU comparison
│   ├── ml_optuna.py          Bayesian optimization (50 trials)
│   ├── ml_lstm.py            LSTM sequence model
│   └── analyze.py            DuckDB analytical queries
├── scripts/
│   ├── run_daily.sh          Production pipeline (fetch→features→score→alerts)
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
    ├── KEY_OBJECTIVES.md    Canonical mission — what the system is for and its non-goals
    ├── MODEL_RISK.md        Model-risk register + monitoring
    ├── PRODUCT_ROADMAP.md   Research arc (completed) + active product roadmap
    ├── SESSION_LOG.md       Session-by-session build log
    ├── SESSION_ARCHIVE.md   Historical session archive
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
| Telegram Bot API | Push alerts (morning + close + narrative) |
| scikit-learn / XGBoost / PyTorch / Optuna | Validated-foundations research layer |
| MLflow | Experiment tracking (localhost:5000) |
| pytest | 20-test pipeline validation suite |
| AWS EC2 + cron | Production hosting + daily automation |
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

# Manage the universe
python manage_universe.py --list
python manage_universe.py --add TICKER --sector ETF --broad SPY

# Explore signals
python daily_signals.py          # console summary
python sector_rotation.py        # top-down sector + laggard scan
streamlit run dashboard.py       # interactive dashboard (port 8501)

---

## 📊 Universe

99 tickers across full GICS sector coverage plus thematic baskets — built to support
top-down sector rotation and secular-theme analysis, not just single-name signals.
Includes **TLT** (20yr Treasury — a bond-market regime signal, not a position) and
**MP** (rare earths). Managed via `manage_universe.py` → `universe.yaml`.

| Segment | Examples |
|---|---|
| Semiconductors (SMH) | NVDA, AVGO, TSM, AMD, AMAT, LRCX, ASML, ARM |
| Software / security (IGV) | MSFT, CRM, NOW, ORCL, PANW, CRWD, PLTR, SNOW |
| Comm / consumer tech (XLC, XLY) | AAPL, GOOG, META, NFLX, AMZN, COST, TSLA |
| Industrials / infra (XLI, PAVE, GRID) | CAT, GEV, PWR, VRT |
| Aerospace / space / quantum (ITA) | RTX, AXON, RKLB, ASTS, IONQ, RGTI |
| Energy / uranium (XLE, URA) | XOM, CVX, FANG, CCJ, CEG, SMR |
| Financials (XLF) | JPM, SOFI, HOOD, MSTR |
| Materials / rare earths (XLB) | FCX, MP, GLW, LITE |
| Macro / sector & broad ETFs | TLT, SPY, QQQ, IWM, XLK, XLV, XLP, GLD, EEM, + more |

---

## 🧪 How It Was Built — Validated Foundations

The product rests on an empirical research phase (Sessions 1–21) that earned every
piece of the signal stack. This is the origin story, not the mission — the full arc
is in [docs/PRODUCT_ROADMAP.md](docs/PRODUCT_ROADMAP.md).

### The Widell Line
An original swing-structure state machine built from first principles. Tracks
resistance (swing highs) and support (swing lows) with a confirmed-optimal N=3 bar
window, assigning each bar a state: up, down, or inconclusive. Named after Spencer
Widell.

| State | Bars | 5-Day Return |
|---|---|---|
| Up | 5,031 | +2.38% |
| Inconclusive | 23,333 | +0.95% |
| Down | 2,598 | -0.83% |

Clean separation validated across tech/growth, value/defensive, and market-ETF
segments; spread scales with volatility (tech 3.21%, value 1.61%, market 0.98%).

### VSA bar classification — chapter closed
Six deterministic bar types tested across daily, sequence, and weekly timeframes.
No consistent standalone predictive signal (VSA ranks last in ML importance, 0.08%).
VSA was the theoretical scaffolding that led to the Widell Line.

### ML layer — ceiling found and respected
Using SPY-relative alpha as the target (removes market drift):

| Model | Accuracy | vs Naive (0.368) |
|---|---|---|
| Random Forest | 0.408 | +0.040 |
| XGBoost GPU | 0.413 | +0.045 |
| XGBoost + Optuna | 0.417 | +0.049 |
| LSTM GPU | 0.412 | +0.044 |

Top features: dist_52w_high (24.9%), dist_52w_low (21.4%), with the Widell Line
ranking 1st/2nd among non-momentum features (wl_encoded 11.1%, score_wl 10.5%).
The edge is the interpreted signal stack, not a black-box predictor — so the product
builds on the validated signals rather than chasing a higher AUC.

### The 2022 lesson
A combined signal once showed +11.53% average — but stress-testing revealed it was
entirely driven by 2022 bear-market snapbacks. Headline results are always broken
down by year and regime. This discipline carries into production: the narrative
treats flips in weak tape or around macro events as likely noise.

---

## 📖 Documentation

- Mission & non-goals — [docs/KEY_OBJECTIVES.md](docs/KEY_OBJECTIVES.md)
- Model-risk register & monitoring — [docs/MODEL_RISK.md](docs/MODEL_RISK.md)
- Research arc + active product roadmap — [docs/PRODUCT_ROADMAP.md](docs/PRODUCT_ROADMAP.md)
- Architectural decisions — [docs/DECISIONS.md](docs/DECISIONS.md)
- Session-by-session build log — [docs/SESSION_LOG.md](docs/SESSION_LOG.md)

---

## 👤 Author

**Spencer Widell** — creator of the Widell Line, an original empirical
swing-structure framework validated across 6 years and 3 market segments, now the
spine of a personal investing intelligence system that turns validated signals into
plain-English decisions.

---

**Disclaimer:** This system is a personal decision-support tool, **not financial
advice**. It never places trades — every output is advisory and the investor makes
the call. Signals are empirical observations on historical data; past performance
does not predict future results.
