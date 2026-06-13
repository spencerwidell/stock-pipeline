# Project Decisions

A record of choices made and why — so future sessions don't
relitigate settled questions. Most recent first.

---

## Vision & Direction

**Session 35 — Project vision shift: research platform → production decision-support system**
The empirical research phase is complete. The Widell Line, conviction scoring, and
the signal stack are validated foundations. The mission is now to **interpret this
stack into plain-English decisions for a concentrated conviction investor** — wide
moats, secular trends toward the future, cash-flowing now, held in a concentrated
portfolio of ~10 best-in-class names. All future development serves this mission;
research was the means, the product is the end. See `docs/KEY_OBJECTIVES.md` for the
canonical statement and `docs/PRODUCT_ROADMAP.md` for the active roadmap.

---

## Portfolio decisioning model (Sessions 45–52)

How the system turns the signal stack into action evolved from "a list of suggestions"
into one decisive, cash-aware plan. The driving feedback: *too many choices, would run
out of cash; make me more concentrated and decisive, not give me a longer menu.*

**The diary records both halves of a trade, and logging keeps `holdings.yaml` in sync**
*(Session 45).* The old single `weight` column was ambiguous (was "8%" the add amount or
the resulting size?). Split into `trade_pct` (signed) + `new_weight` (resulting size).
Logging now writes `new_weight` back into `holdings.yaml` via `holdings_io.apply_trade`
(CASH offsets so the book stays at 100%), so the snapshot can't go stale. `holdings.yaml`
is still the one hand-maintained file — it's just kept current automatically now.

**One place to act; every other tab is read-only context** *(Sessions 42, 46).* The
Briefing had three disagreeing action lists, and the Sizing tab's normalized-target
rebalance told the investor to trim cheap, high-conviction cores. Decision: every
actionable item flows through ONE engine onto ONE surface (the Briefing). Sizing became
the read-only **Destination Book** map; Themes and Tide are context. No parallel lists.

**The Destination Book — concentrate & complete** *(Session 47).* The system is now
organized around the portfolio being *built toward*: held CORE names at conviction-led
target weights (water-fill to 100−reserve, cap 15%). Recommendations are the *next step*
toward it, in one cash-aware queue that completes the underweight winners before opening
new positions, and never recommends more than the available cash funds.

**Be decisive — sell non-core, no manual overrides** *(Session 47).* A held name that
fails core conviction and is low-quality (moat≤2 & fund≤2) or off-thesis (no theme) gets
a **full SELL**, not a trim-to-rump. A non-core name with a real edge sits in a
**speculative sleeve under the −7% stop**. The `overrides` block was emptied (TSLA's
`core` override dropped) — a name earns CORE on the evidence or it doesn't. "Let the
system work." REDUCE fires only on a name that's overweight *and* low-conviction, so the
system never nags a trim on a winner.

**The Tide paces deployment; it never moves the destination** *(Session 48).* A top-down
regime (rising/neutral/falling) from the benchmarks + sector breadth + TLT sets the cash
reserve (5/8/12%) and, in a falling tide, defers adds whose sector is sinking. The
*targets* keep a fixed 8% reserve so the destination doesn't churn when the tide flips —
only the *pace* of getting there changes. "Don't fight the tide."

**One synthesized voice — Idea of the Day + an aligned narrative** *(Sessions 50–51).*
The system was producing a decisive cockpit but still narrating off the old engines. Two
moves closed it: an **Idea of the Day** (`idea_of_the_day.py`) — ONE insight per day via
a priority ladder (stop hit → thesis break → tide turn → top step → patience), framed by
the tide, on a 💡 Briefing card and a morning phone push; and rewiring `narrative_alert.py`
to feed Claude the SAME engines as the cockpit (Tide + Idea + Destination Next Steps) with
a prompt that speaks the decisive, concentrate-&-complete, tide-aware language. The morning
Idea, the dashboard cockpit, and the close narrative now all reason off the same engines —
one voice end to end. (The raw Signals tab was de-emphasized to reference, Session 52.)

**Deploy discipline — never blind-`git checkout` `holdings.yaml` on AWS** *(Session 47).*
It's dashboard-written, so AWS is often the newer truth. A faulty reconcile once clobbered
a live trade (recovered via the append-only diary). Always check `git diff --quiet` (real
exit code) and cross-check the diary before reconciling. The recurring manual reconcile is
the strongest case for the GitHub-auto-backup token.

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
- Documented in PRODUCT_ROADMAP.md (Part 1 — Research Arc)

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

## Signal Synthesis & Top-Down Workflow

**Conviction score is a buy-zone quality metric, distinct from composite (Session 30)**
Composite (-6 to +6) measures momentum/signal *direction*; conviction (0-10)
measures *entry quality* — where price sits in its channel, what you'd own
(fundamentals), and timing (state + flip recency). They are intentionally
separate axes: a name can be high-composite but low-conviction (strong but
extended) or low-composite but high-conviction (quality name resting low in
its channel). Keeping them separate avoids collapsing "should I act" into a
single number that hides the trade-off.

**Top-down sector rotation as the second analytical layer (Session 30)**
Single-name signals don't say whether the *sector* is the place to be.
sector_rotation.py ranks the 23 sector/thematic ETFs by opportunity, then
drills into favorable ones for quality laggards (ROOM_TO_RUN / LAGGING / BOTH).
This makes the workflow top-down: pick the sector, then the name within it.

**Rotation logic lives in sector_rotation.py; the dashboard tab is a port, not a fork (Session 31)**
The Rotation dashboard tab reuses the same sector_map source of truth and
mirrors the CLI scanner's ranking + laggard rules exactly. Decision: never let
the tab and the CLI scanner diverge — when one changes, the other must match
(conviction_score was added to the CLI Section B in the same session precisely
to keep them aligned). One set of rules, two surfaces.

## Signal Delivery & Automation

**Two delivery surfaces: Streamlit dashboard (explore) + Telegram (push)**
The dashboard on AWS is for sitting down and exploring; Telegram is for being
told what matters without opening anything. Same underlying parquet, different
interaction modes.

**Two-cron architecture: morning live check + evening full pipeline (Session 31)**
- 14:30 UTC (10:30 AM ET): morning_alert.py — no pipeline re-run, just live
  Polygon snapshot prices measured against *yesterday's* computed levels.
  Answers "what's actionable right now."
- 21:30 UTC (4:30 PM ET): run_daily.sh — full feature recompute + close alert.
  Answers "what is true as of today's close."
Separating "recompute features" (expensive, end-of-day) from "check live prices
against known levels" (cheap, intraday) keeps the morning check lightweight.

**Morning alert always sends; daily alert is gated by SEND_TELEGRAM (Session 31)**
The daily pipeline's Telegram push is opt-in (SEND_TELEGRAM=1, set only in the
AWS cron) so local/manual runs don't ping the phone. The morning alert has no
gate and sends a heartbeat ("Nothing actionable this morning") even when empty —
its whole purpose is the morning ping, so silence would be ambiguous with
failure.

---

## Intelligence Layer — LLM, Fundamentals, Themes (Sessions 32–35)

**LLM narrative briefing is interpretation, not new signal (Session 32)**
`narrative_alert.py` (a 3rd daily Telegram message) sends all signals to Claude
(`claude-sonnet-4-6`) to produce plain-English MARKET CONTEXT / ACTIONABLE SETUPS /
WATCH LIST / PORTFOLIO CHECK / BOTTOM LINE. The system already *produces* signals;
the gap was *interpretation* ("15 flips, conv 8 — so what?"). The LLM only reasons
over provided structured context; it never invents data. Fail-soft: any API error
logs and skips so the pipeline never breaks.

**Sonnet for the daily narrative, Opus for quarterly moat (Sessions 32, 34)**
The daily briefing uses Sonnet (cost — runs every close). Moat scoring uses
`claude-opus-4-8` (quality judgment, runs only quarterly so the better model is
affordable). The roadmap's `claude-sonnet-4-20250514` was days from retirement —
always pin a current model ID.

**Earnings via yfinance, not Polygon (Session 32)**
Polygon's *forward* earnings dates require the Benzinga add-on (not on this plan);
yfinance is the free path to future earnings. `fetch_earnings.py` self-throttles
(weekly) so it's safe to call daily.

**holdings.yaml is a weight snapshot; CASH is dry powder (Session 32)**
No transaction ledger — just current weights, hand-updated. CASH is surfaced to the
narrative as deployable dry powder for buy-vs-wait sizing.

**Valuation is context, not part of conviction (Session 34)**
PE/PEG/P-OCF (`valuation.py`) inform the narrative and dashboard but do NOT feed the
conviction score — a deliberate choice to keep conviction a clean buy-zone-quality
metric. P-OCF stands in for P/FCF because Polygon doesn't expose capex; it's labeled
a proxy. Sanity guards drop implausible ratios (bad price/shares).

**universe.yaml is the single source of truth (Session 34)**
`fetch_stock.py` and `sector_map.py` read `universe.yaml`; `manage_universe.py`
(`--add/--remove/--list`) edits it. No more hardcoded ticker lists. "Owned" is
derived from holdings.yaml — no separate core/watchlist tiers to drift.

**Exit/trim is a status, not a hard stop (Session 34)**
`positions.py` classifies held names TRIM (above channel top) / REVIEW (breakdown +
Widell down) / HOLD — long-term framing, no hard stops. Surfaced as the narrative
PORTFOLIO CHECK section and a morning POSITION CHECK.

**Macro is hand-maintained calendar context, not a fetched feed (Session 35)**
`macro_calendar.yaml` (CPI/FOMC) is hand-curated; the narrative treats fresh flips
near a CPI/Fed event as likely noise — the Session 32 lesson operationalized.

**Themes are a human-curated thesis layer, surfaced not scored (Session 35)**
`themes.yaml` maps names to ~11 secular trends; `theme_engine.py` overlays live
signals to show coverage, gaps, concentration, off-thesis holdings, best-entry-now,
and the TLT bond regime. It informs (dashboard Themes tab + narrative context) but
does not alter the conviction score. The ⭐ "fits profile" flag encodes Spencer's
ideal: wide moat × secular trend × cash-flowing now.

**Read-only public dashboard — no API-spending controls (Session 33)**
The dashboard is publicly reachable with no auth, so it must never expose a control
that spends the Claude API key (regenerate, Q&A). It only displays artifacts
generated server-side by the trusted cron. Interactive features wait for auth.

**Dashboard password gate — app-level auth, not IP allowlist (Session 35)**
Chose a single app-level password (DASHBOARD_PASSWORD in .env, constant-time
compare, fail-closed) over an AWS security-group IP allowlist because the dashboard
is accessed from a phone on changing mobile IPs — a password works from any device.
Gates the WHOLE app before any data renders, so holdings are never exposed.
Fail-closed: if the secret is unset the app stays locked. Recovery is always
available (the owner controls .env via SSH). Multi-user/guest read-only mode is
deferred until interactive Q&A ships.

**Position sizing is advisory and conviction-led, never mechanical (Session 35)**
Target weights are a *suggestion to inform decisions*, never an auto-rebalance — the
system never trades. Score is conviction-led (conviction + theme conviction + moat +
valuation + ⭐ fits-profile). Held names are rebalanced by normalizing across the
*currently-invested %* (cash held constant — respected as deliberate dry powder),
not by deploying cash. Gap starters (best-in-class in uncovered high/medium-conviction
themes) are surfaced *separately* with a modest suggested size, explicitly funded
from cash or trims — never auto-mixed into the held pie (so it won't suggest trimming
a great holding to fund an unproven idea). Caps: 15% max position, 4% min starter.

**Holdings is the only hand-maintained file; everything else is derived (Session 36)**
Spencer maintains exactly one file — `holdings.yaml` (now `portfolio:` / `positions:` /
`overrides:`). CORE/SPECULATIVE tier, theme mapping, 7% stop tracking, and cash
deployment are all DERIVED fresh at dashboard load and pipeline close — never stored,
never hand-edited. A single shared reader (`holdings_io.py`) replaced six divergent
`load_holdings()` copies so there's one parse of the file. Rationale: the system should
ask the investor for the minimum (what he owns) and compute everything else, so nothing
drifts out of sync and there's no manual upkeep beyond updating weights after a trade.

**CORE vs SPECULATIVE is evidence-based, with a deliberate drawdown carve-out (Session 36)**
`auto_classify.py` tiers each holding: CORE requires ALL of moat ≥4, fundamental ≥4
(missing F doesn't block — international names), a high/medium-conviction theme, and
weight >2%; else SPECULATIVE, with the failing reasons shown. Overrides in holdings.yaml
always win. Key carve-out: a name that is otherwise core-quality but down ≥40% from its
high STAYS core (a buy-weakness signal), and the −40% rule only demotes names that don't
otherwise earn core. This encodes the standing rule that *price level alone is never a
core exit trigger* — only a broken thesis is. Stops are tracked for SPECULATIVE names
only; core weakness is a buy signal, never a stop.

**Cash deployment is priority-ordered, advisory, cash-only (Session 36)**
`cash_deployment.py` answers "where does my next dollar go" in four priority steps: add
to core on weakness → fill a high-conviction theme gap at entry → beaten-down quality
(speculative) → else hold cash and show the trigger price. Deployment is funded from
cash only (drops are flagged, never assumed sold); speculative buys carry a −7% stop
anchored on first-seen entry price (`data/positions_seen.json`, system-maintained).
Pacing favors staged tranches into pullbacks. It never trades — human-in-the-loop.

**Fundamental scoring is sector-aware, not one rubric (Session 37)**
One software-tuned rubric (rev>20, gross>50, op>15, eps>10, +OCF) mis-scored entire
business categories — banks have no gross margin (they run on ROE/efficiency), energy is
cyclical, and low-margin-by-design mega-caps (AMZN, COST) looked weak. `business_model.py`
assigns each name a business archetype (software / platform / financial / energy /
industrial / staple / consumer / pre-profit) and grades it on the metrics that fit, on
the same 0–5 scale so conviction and classification are unchanged. `pre_profit` is
data-driven (no TTM earnings AND no operating cash — a GAAP loss alone doesn't qualify,
so cash-generative SaaS stays in software). This fixed AMZN/JPM/XOM/CMI on evidence and
made AMZN core without a per-name override — the honest fix over hard-coding exceptions.

**Forward PE is our own run-rate projection, not an analyst feed (Session 37)**
Forward valuation uses a bear/base/bull EPS-growth band computed from four historical
YoY readings (each recent quarter vs the same quarter a year prior; base = median, robust
to one outlier), turned into a forward PE band live against price (`valuation.compute_forward`).
Chosen over yfinance/analyst estimates because it's deterministic, transparent, fits the
project's first-principles ethos, and the band itself communicates uncertainty (a rising
forward PE flags an earnings decline; a 400× flags a story stock). None for pre-profit
names (TTM EPS ≤ 0).

**Conviction re-weighted: Widell-state-led, breakdowns not rewarded (Session 40)**
The Session 35 backtest showed the original weighting (channel `lower=4`/`breakdown=2`,
Widell state 0–2, fundamentals 0–3) rewarded beaten-down beta and under-weighted the
*validated* Widell-state edge — the mid-scale 0–3 bucket beat 4–5 and 6–7. We tested four
candidate schemes on 100k+ bars of SPY-relative forward alpha and adopted the winner:
**Widell state 0–4** (top driver; ≥8 now requires confirmed up-momentum), **channel 0–3**
with **breakdown/extended = 0** (broken structure isn't a buy-the-dip), **fundamentals
0–2** (lighter weight on the only lookahead-prone component), flip 0–1. Result: Spearman
+0.0259 → +0.0333, monotonic win rate, and a ≥8 bucket that beats the rest in nearly every
year incl. the 2022 bear (+13.7%). Honest limit kept: it's a top-tier filter (≥8), not a
linear dial — the mid-scale is coarse context, and ≥8 is correctly sparse in a weak tape.
`cash_deployment.CORE_WEAK_CONV` lowered 6 → 5 to match the new scale (a down-state core
pullback now tops out ~5–6). See `docs/CONVICTION_BACKTEST.md`.

**Universe manager + investor diary; AWS-authoritative state (Session 41)**
Two simple, high-leverage features Spencer asked for: a no-terminal way to add/remove
companies (⚙️ Manage tab over the existing `manage_universe.cmd_add/cmd_remove`) and a
lightweight investor diary (`diary.py` — append-only `investor_diary.csv`, fixed schema
date/ticker/action/weight/recommendation/note, with ✅ Log buttons on the Briefing
actions). The diary is the ACTION HISTORY; holdings.yaml stays the current-weight
SNAPSHOT (the standing one-file-you-maintain rule is unchanged). Both features spend no
Claude API and sit behind the password gate, so the no-public-API-controls rule holds.

**State-sync decision:** AWS cannot push to GitHub (HTTPS remote, no stored token), so
the planned nightly cron commit+push isn't available without a one-time PAT/deploy key.
Adopted the pragmatic model instead: the **diary is gitignored and AWS-authoritative**
(persistent EC2 instance is the source of truth; a Download button is the backup), and
**universe.yaml edits made on the dashboard are reconciled with git at deploy time**
(infrequent, handled manually). Full GitHub auto-backup of these two files is an optional
follow-up gated only on Spencer creating a repo token.

**One consolidated action model; the engine is the source of truth (Session 42)**
The Briefing had three overlapping recommendation surfaces that disagreed: the
deterministic `cash_deployment` cockpit (loggable, but showed only its top 3, no trims,
no macro timing), and the LLM narrative's ACTIONABLE SETUPS (conv≥8 names) + PORTFOLIO
CHECK (trims) — different names, none loggable. Resolved by making `cash_deployment` the
single source of truth: one ranked, macro-aware action model covering every actionable
type (add-to-core, NEW SETUP at conv≥8, gap starter, TRIM/REVIEW, beaten-down), each
with a priority rank and NOW/WAIT timing (a CPI/FOMC within 3 days or an extended entry
→ WAIT → watchlist). The dashboard shows 🎯 Portfolio Action (the one ranked, loggable
NOW list) + 👀 Watchlist; the narrative is reduced to four sections (MARKET CONTEXT /
PORTFOLIO ACTION / WATCHLIST / BOTTOM LINE) and is forbidden to invent a parallel list —
it translates the engine and adds the macro "why". **A conv≥8 best-in-class name in a
theme he's light on is deliberate breadth across secular trends (Spencer's call), a real
buy candidate, not dilution** — so it's an action (ranked), not buried. Position count
vs the 10-15 target is shown so concentration stays visible without blocking.

---

*Add new decisions here as the project evolves.*
