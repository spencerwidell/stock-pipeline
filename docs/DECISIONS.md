# Project Decisions

A record of choices made and why — so future sessions don't
relitigate settled questions.

---

## Environment

**WSL over plain Windows terminal**
Chose WSL because all DS tooling, cloud servers, Docker, and
interview expectations assume Unix/Linux bash. PowerShell commands
don't transfer. One-time setup cost, permanent payoff.

**Ubuntu app to open terminal, not `wsl` from PowerShell**
The `wsl` command starts a non-login shell that doesn't fully
load `.bashrc`, so conda doesn't activate. Ubuntu app starts
a login shell — consistent, correct every time.

**Miniconda over Anaconda**
Anaconda bundles ~3GB of packages, most of which we don't need.
Miniconda is ~150MB and installs only what you explicitly ask for.
Keeps the environment clean and intentional.

## Project structure

**Projects live on the Linux side (`/home/datasci/projects/`)**
Not on the Windows side (`/mnt/c/...`). Linux filesystem
performance in WSL is significantly faster for file-heavy
operations like reading Parquet. Keep all active project work here.

**One conda environment per project (`stock`)**
Never install project packages into `base`. Isolated environments
prevent dependency conflicts and make projects reproducible.

## Git / GitHub

**HTTPS over SSH for GitHub remote**
Simpler setup for a learning environment. SSH would require
key generation and GitHub configuration. HTTPS with credential
store achieves the same result with less setup friction.

**Credential store for authentication**
`git config --global credential.helper store` saves the PAT
token to disk after first use. Fine for a personal machine.

**Public repository**
Project is a learning portfolio piece targeting a lead DS role.
Public visibility is intentional — it's the point.

## Security

**API keys in `.env`, never in code**
`.env` file holds `POLYGON_API_KEY=...` and is listed in
`.gitignore` so Git never sees it. Script reads key into memory
at runtime.

**Personal Access Token for GitHub**
GitHub deprecated password auth for Git operations in 2021.
PAT generated with `repo` scope only — minimum permissions needed.

---

## AI Tooling

**Claude Code over GitHub Copilot**
Already included in Max $200/month plan — no additional cost.
Runs in WSL terminal, aligns with CLI learning goals, supports
agentic workflows.

---

## Data Storage & Querying

**DuckDB over PostgreSQL**
Embedded database — no server process to manage, no authentication.
Queries Parquet files directly without import/ETL steps.
Full SQL support for analytics (window functions, CTEs, aggregations).
Perfect fit for single-user research environment on WSL.

**Parquet as the storage format**
Columnar, compressed, schema-preserving. DuckDB reads it natively.
Types preserved across read/write cycles unlike CSV.

---

## Research Framework

**VSA before Classic Wyckoff**
Starting with Volume Spread Analysis (bar-by-bar classification)
before progressing to full Wyckoff phase detection because:
- VSA features are deterministic, SQL-computable, and interpretable
- Can't detect accumulation phases without first detecting bars
- Documented in RESEARCH_ROADMAP.md

**VSA chapter closed (Sessions 7-17)**
Empirical testing across daily next-day, daily 5-10 day, consecutive
sequences, and weekly bars found no consistent standalone predictive
signal. VSA labels rank last in ML feature importance (0.08%).
VSA served as the theoretical scaffolding that led to the Widell Line.

**The Widell Line as the primary contribution (Session 11)**
Original swing-structure state machine built from first principles.
N=3 swing window empirically confirmed as optimal via widell_optimize.py.
Three states (up/down/inconclusive) show clean, consistent separation:
- up: +2.38% 5-day return
- inconclusive: +0.95%
- down: -0.83%
Validated across all three market segments (tech, value, market ETFs).
Named after Spencer Widell — original empirical framework.

**SPY-relative alpha as ML target (Session 18)**
Switching from raw 5-day return to SPY-relative alpha removed market
drift and lowered naive baseline from 0.443 to 0.368. This produced
the first above-baseline ML result (0.412 vs 0.368 naive).

**XGBoost over Random Forest (Session 19)**
XGBoost finds feature interactions that Random Forest misses.
Widell Line features (wl_encoded, score_wl) rank #1 and #2 in
XGBoost importance vs buried in Random Forest. GPU-accelerated
via device=cuda on RTX 4090.

**Optuna over manual grid search (Session 19)**
Bayesian optimization explores parameter space efficiently.
50 trials found best params: depth=4, lr=0.046, n_est=337.
Best accuracy: 0.417.

**LSTM does not outperform XGBoost (Session 20)**
LSTM with 20-bar sequence length achieved 0.412 — identical to
XGBoost. Temporal patterns in daily OHLCV-derived features are
not complex enough to justify sequence model overhead.
XGBoost + engineered sequence features captures the same information.

**ML ceiling at ~0.417 with current data (Session 20)**
All models cluster 0.408-0.417. Further gains require:
- More tickers (broader universe)
- New data types (options flow, sentiment, fundamentals)
- Longer history

**52-week high/low distance as dominant ML features (Session 18)**
dist_52w_high and dist_52w_low dominate feature importance at 24.9%
and 21.4% respectively. These capture the well-known 52-week high
effect (George & Hwang, 2004). The Widell Line adds incremental
value on top of this momentum factor.

**Pytest test suite (Session 19)**
20 tests covering data integrity, feature ranges, regime values,
VSA labels, Widell Line state separation, and pipeline consistency.
Run after every pipeline change: `pytest tests/ -v`

**MLflow for experiment tracking**
All ML experiments logged to local SQLite (mlflow.db) and mlruns/.
Both gitignored. UI accessible at localhost:5000 via:
`mlflow ui --host 0.0.0.0 --port 5000`

---

*Add new decisions here as the project evolves.*
