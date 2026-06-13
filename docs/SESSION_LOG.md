# Session Log — Stock Pipeline Project

**Phase orientation (read first):**
- **Sessions 1–21:** Research and validation phase — earning the foundations.
- **Sessions 22+:** Production system development — turning signals into a live product.
- **Sessions 35+:** Decision-support system evolution — interpreting the stack into
  plain-English decisions for a concentrated conviction investor (see
  `docs/KEY_OBJECTIVES.md`).

For sessions 1-24 see docs/SESSION_ARCHIVE.md

---

## 📍 Current state & open items (as of Session 42, June 12 2026)

**What the system is now:** you maintain ONE file (`holdings.yaml`); the system derives
tier (CORE/SPECULATIVE), theme coverage, cash-deployment priorities, 7% stops, and grades
every business on the metrics that fit it — with a forward-PE band it projects itself.
Deployed on AWS (password-gated), three Telegram alerts + an eight-tab dashboard.

**Shipped recently (all deployed):**
- **S36 — Portfolio intelligence:** `holdings_io` / `auto_classify` (CORE vs SPECULATIVE)
  / `cash_deployment` ("where the next dollar goes" + speculative stops + thesis integrity);
  🧠 Briefing cockpit, narrative PORTFOLIO ACTION, tier-aware morning checks.
- **S37 — Sector-aware fundamentals:** `business_model.py` archetype rubrics (banks on
  ROE/efficiency, energy on cash flow, …) + our own forward-PE band. Fixed AMZN/JPM/XOM
  on evidence → AMZN core without an override.
- **S38 — Interactive Q&A:** `qa_engine.py` + 💬 Ask tab, reuses the alert builders,
  signals-only, behind the password.
- **S39 — Data-quality:** removed BKNG (corrupt ~30× price feed); made forward growth
  split-safe via fiscal-period-matched net income (fixes NVDA forward PE).
- **S40 — Conviction re-weight:** backtest-driven — Widell state now the top driver
  (≥8 requires up-momentum), breakdowns no longer rewarded, fundamental weight 3→2.
  Better Spearman, monotonic win rate, ≥8 +13.7% in the 2022 bear.
- **S41 — Manage tab:** dashboard universe add/remove (over `manage_universe`) + a
  lightweight investor diary (`diary.py`, gitignored, ✅ Log buttons on Briefing).
- **S42 — Consolidated recommendations:** one ranked, macro-aware action model in
  `cash_deployment` (adds/new-setups/gap-starters/trims/beaten-down, NOW vs WAIT) →
  🎯 Portfolio Action + 👀 Watchlist on the Briefing; narrative cut to 4 sections,
  engine is the single source of truth (no more parallel/disagreeing lists).

**Next steps (priority order):**
1. **Narrative-quality review** — after a week of live runs in the new format.
2. **Q&A enhancements (optional)** — a news source + multi-user guest mode with a rate guard.
3. **GitHub auto-backup of universe.yaml + diary (optional)** — needs a one-time
   GitHub token/deploy key on AWS so a nightly cron can commit+push them (AWS can't push
   today). Until then the diary is AWS-local + Download button, and universe.yaml is
   reconciled with git at deploy time.
4. **Remove the fundamental lookahead fully** — needs point-in-time fundamentals history.
5. **Watch:** confirm the nightly close keeps `positions_seen.json` + the narrative healthy.

---

## Project state (as of Session 13)

**Environment:** WSL Ubuntu 22.04, conda env `stock` (Python 3.11)
**GitHub:** github.com/spencerwidell/stock-pipeline
**Stack:** Polygon.io API → fetch_stock.py → Parquet → DuckDB → analysis

**Files:**
- `fetch_stock.py` — fetches 22 tickers, 6 years, saves to Parquet
- `vsa_features.py` — direction, spread, rel_spread, rel_volume,
  ma20/50/200, dist_ma200, ma200_slope, regime, channel_pos
- `vsa_labels.py` — classifies bars into 6 VSA types + neutral
- `widell_line.py` — swing state machine, wl_state, wl_flip
- `analyze.py` — DuckDB queries
- `scripts/morning_startup.sh` — health check + git pull
- `scripts/run_pipeline.sh` — nohup fetch with timestamped logging

**Data:**
- `data/stock_ohlcv.parquet` — 30,962 rows, 21 tickers, 6 years
- `data/stock_vsa.parquet` — full feature set including Widell Line

**Universe:**
- Tech/growth (15): AMZN, NVDA, MSFT, META, TSLA, ELF, CELH,
  PLTR, AVGO, SOFI, TSM, NOW, IBM, CRM, ORCL
- Market (2): SPY, QQQ
- Value/defensive (4): JPM, PG, XOM, GLD
- BRK-B: failed (Polygon symbol issue, investigate later)

**Pipeline order (must run in sequence):**
1. `python vsa_features.py`
2. `python vsa_labels.py`
3. `python widell_line.py`

---

---

## AWS deploy workflow
- Local changes → git push
- AWS: git checkout -- <file> if conflicts, then git pull
- sudo systemctl restart streamlit
- One-liner: ssh -i ~/.ssh/stock-pipeline-key.pem ubuntu@18.188.180.99 "cd ~/stock-pipeline && git pull && sudo systemctl restart streamlit"

---

---

## Session 25 — June 9, 2026

**AWS EC2 deployment — fully operational**

**Infrastructure:**
- Instance: t3.micro, Ubuntu 24.04, US-East-2 (Ohio)
- IP: 18.188.180.99
- Storage: 30GB
- Free tier: 12 months

**What's running on the server:**
- Full pipeline: fetch → vsa_features → vsa_labels → widell_line → composite_score
- 20/20 pytest tests passing
- Cron job: 9:30 PM UTC (4:30 PM Eastern) weekdays — fully automatic
- Streamlit dashboard: http://18.188.180.99:8501 — accessible from any device
- Systemd service keeps dashboard alive permanently, restarts on reboot

**Key files on server:**
- ~/stock-pipeline/ — full repo clone
- ~/.env — Polygon API key (copied manually, not in Git)
- /etc/systemd/system/streamlit.service — dashboard auto-start
- crontab — daily pipeline automation

**Access:**
- Dashboard: http://18.188.180.99:8501 (any browser, any device)
- SSH: ssh -i ~/.ssh/stock-pipeline-key.pem ubuntu@18.188.180.99

---

---

## Session 26 — June 9, 2026

**Built:** Gap from flip and pullback target features

**New features added:**
- flip_price: price at the moment of Widell state flip (widell_line.py)
- flip_date: date of the last flip
- pullback_target: resistance level broken at flip (where old resistance = new support)
- gap_from_flip: % move since flip day (are you chasing?)

**Daily signals enhanced:**
- Flips section now shows gap and pullback target
- New "Up State — Entry & Pullback Analysis" section
- Color coded: 🟢 AT ENTRY (<2%), 🟡 ELEVATED (2-5%), 🔴 CHASING (>5%)

**Dashboard updated:**
- Same gap/pullback intelligence in Streamlit
- New up state section with chase indicator
- gap_from_flip column color coded in table
- Guide tab updated with gap explanation and example

**AWS deployment:**
- git pull + systemctl restart streamlit workflow established
- One-liner deploy from AWS terminal: git pull && sudo systemctl restart streamlit

**Real world validation:**
- AMAT: gap=+9.4%, pullback→$448 — chasing territory
- ASML/CAT: Day 1 flips, gap near 0% — entry zone
- System correctly identified the semi equipment sector rotation

**Key workflow for tomorrow:**
- Check dashboard after 4:30 PM ET for fresh data
- Up State section shows today's actual gaps
- If ASML/CAT still in up state with gap < 5% — validated entry

---

---

## Session 27 — June 9, 2026

**Built:** telegram_alert.py — daily push notifications

**Telegram bot setup:**
- Bot: @widell_line_bot (Widell Line Signals)
- Token stored in .env (never in Git)
- Chat ID stored in .env

**Alert content:**
- Daily summary: up/inconclusive/down counts + flip count
- Flips today with state, score, gap from flip
- Up state analysis: entry/elevated/chasing status + pullback target
- High score opportunities (≥2, not yet up)
- Dashboard link

**AWS cron updated:**
- Pipeline + telegram_alert.py runs at 9:30 PM UTC (4:30 PM ET) weekdays
- Fully automated end to end — no laptop required

**Complete automated workflow:**
Polygon API → features → labels → Widell Line → composite score
→ Telegram alert on phone → Dashboard for full details

---

---

## Session 28 — June 9, 2026

**Built:** 200-day linear regression channel

**New features in vsa_features.py:**
- reg_center: best-fit trend line (200-day linear regression)
- reg_upper: center + 1 standard deviation
- reg_lower: center - 1 standard deviation
- channel_pos: position within channel (0=lower, 0.5=center, 1.0=upper, >1=extended)

**New feature in composite_score.py:**
- channel_zone: extended / upper / middle / lower / breakdown

**Signal enhancements:**
- Up state section now shows channel zone icon
- 🔴 CHASING+EXT = both gap>5% AND extended above channel
- CAT/JPM: AT ENTRY, upper zone — clean setups
- AMAT/AXON: CHASING+EXT — strongest avoid signal
- XLV: AT ENTRY, middle zone — best risk/reward

**Dashboard enhancements:**
- Ticker History now shows price with regression channel
- Four lines: close, reg_upper, reg_center, reg_lower
- Channel zone label shown below chart
- RSI chart added alongside composite

**Backtest v4 findings:**
- Gap filter adds no value systematically (flip day gap always 0%)
- Day 2 validation consistently worse (-73% vs BAH on 15 names)
- Gap intelligence most valuable for manual decision making
- Full universe: system +475.8% vs BAH +474.0% — razor thin edge
- System edge concentrated in volatile growth names, not uniform

**Two-layer framework confirmed:**
- Widell Line: short-term momentum and entry timing
- Regression channel: long-term trend context
- PLTR: inconclusive -2 BUT middle of channel = hold, not exit
- NVDA: down -1 BUT upper channel = normal pullback, not breakdown

---

---

## Session 29 — June 9, 2026

**Built:** fetch_fundamentals.py — Polygon Financials API integration

**Data source:** Polygon vX/reference/financials endpoint
- 67 tickers with data, 21 skipped (ETFs + international: ASML, TSM, ARM, CCJ)
- Quarterly data, 8 quarters fetched per ticker
- Fields: revenue, gross_profit, operating_income, net_income, EPS, operating_CF

**Fundamental score (0-5):**
- Revenue growth YoY > 20%: +1
- Gross margin > 50%: +1
- Operating margin > 15%: +1
- EPS growth YoY > 10%: +1
- Positive operating cash flow: +1

**Score 5 (Elite):** NVDA, AVGO, PLTR, ANET, APP, MU, CRDO, ISRG, ALAB
**Score 4 (Strong):** MSFT, AMD, CAT, CRWD, GOOG, META, CRM, LRCX, VRT, CELH

**Two-layer signal — up state today:**
- CAT: Widell +4, F:4/5, AT ENTRY, upper channel — highest conviction
- AMAT: Widell +3, F:3/5, CHASING+EXT — wait for pullback
- AXON: Widell +2, F:3/5, CHASING+EXT — wait for pullback
- ASML: Widell +4, F:N/A — strong signal, missing fundamentals

**Integrated into:**
- daily_signals.py: F:X/5 shown in up state section
- telegram_alert.py: F:X/5 shown in up state alert
- dashboard.py: new Fundamentals tab (3rd tab)

**fetch_fundamentals.py runs separately (not daily):**
- Run quarterly or after earnings season
- Fundamentals change slowly — no need for daily refresh

---

---

## Session 30 — June 9, 2026

**Built:** sector_rotation.py, conviction_score.py, updated sector_map.py

**New ETFs added to universe (97 tickers total):**
XLK, XLI, XLB, XLY, XLC, ITA, PAVE, GRID, URA — full GICS sector coverage
plus infrastructure and uranium/nuclear thematic.

**sector_map.py — complete rebuild:**
- All 88 universe tickers mapped (zero falling to default)
- Dual mappings first-class: GEV→[XLI, GRID], PWR→[XLI, PAVE]
- Added get_constituents() reverse lookup and SECTOR_ETFS list
- 97 total entries (88 stocks + 9 ETF self-maps)

**sector_rotation.py — two-section rotation scanner:**
- Section A: ranks all 23 ETFs by Widell state + channel zone
  (favorable + low channel at top, extended/broken at bottom)
- Section B: for each ETF in up state or lower/middle channel, surfaces
  F≥3 constituent laggards tagged ROOM_TO_RUN / LAGGING / BOTH,
  sorted by lowest channel_pos
- Today's read: XLI up/middle at top; GLD/URA/XLC broken down at bottom;
  ISRG (F5, lower, BOTH) flagged under XLV; LITE (F4, ROOM_TO_RUN) under XLB

**conviction_score.py — 0–10 score added to stock_vsa.parquet:**

| Layer | Max | Logic |
|---|---|---|
| Channel position | 4 | lower=4, middle=3, upper=1, extended=0, breakdown=2, unknown=1 |
| Fundamentals | 3 | F:5→3, F:4→2, F:3→1, F:0-2→0 |
| Widell state | 2 | up=2, inconclusive=1, down=0 |
| Flip recency | 1 | flipped within 5 bars=1, else=0 |

Score 8+ = highest conviction buy zone (good channel entry + quality
fundamentals + Widell confirming).

**Wired into:**
- daily_signals.py: Conv column + conv=N/10 in up-state analysis
- dashboard.py: 🎯 Conviction ≥8 metric, conviction column with green styling,
  Guide methodology updated
- telegram_alert.py: conv:N/10 in up-state alert lines
- scripts/run_daily.sh: conviction_score.py added after composite_score.py

**AWS deploy — important finding:**
- run_daily.sh hardcoded /home/datasci path — was local-only, never the AWS
  mechanism. AWS production pipeline runs via inline crontab with
  /home/ubuntu/miniconda3
- Crontab patched to insert conviction_score.py before telegram_alert.py
  (backed up to ~/crontab.bak)
- Tonight's 21:30 UTC cron verified safe via telegram dry-run
- **Resolved same session:** made run_daily.sh conda-path-portable (auto-detects
  conda under $HOME/miniconda3, $HOME/anaconda3, /opt/conda) and pointed the AWS
  cron at it (SEND_TELEGRAM=1 bash scripts/run_daily.sh) so the pipeline and the
  cron can no longer drift

**Test suite:** 20/20 passing. GRID low-volume filter fix: test_row_count_preserved
updated to expect vsa == ohlcv[volume>1000].

---

---

## Session 31 — June 10, 2026

**Built:** Rotation tab, High Conviction callout, morning_alert.py, morning cron

**Rotation tab added to dashboard.py (commit 159fadd):**
- 4th tab in the dashboard — 🔄 Rotation
- Section A: all 23 ETFs ranked by Widell state + channel position
  (favorable + low channel first), color-coded
- Section B: F≥3 constituent laggards tagged ROOM_TO_RUN / LAGGING / BOTH,
  sorted by lowest channel_pos, includes conviction_score
- Logic is a faithful port of sector_rotation.py — tab and CLI scanner always
  agree
- conviction_score added to sector_rotation.py Section B CLI output so both
  match

**High Conviction callout added to Signals tab (commit 3b39942):**
- First content block on the Signals tab, above Flips
- Shows all tickers with conviction_score ≥ 8: ticker, state, composite,
  conviction, channel_zone, gap_from_flip, pullback_target, fundamental_score
- Neutral fallback when none qualify
- Today: 1 qualifier (ISRG — inconclusive, lower channel, F:5)

**morning_alert.py — new script (commit 3b39942):**
- Lightweight morning check, no pipeline re-run
- Loads latest bar per ticker, fetches live prices via Polygon bulk snapshot
  endpoint
- Three Telegram sections:
  - High Conviction in Entry Range: conv≥8 within 3% of pullback target —
    actionable now
  - Breakout Watch: inconclusive within 5% of breakout level, moved >1% at open
  - Notable Moves: any ticker ±3% at open, context only
- Heartbeat message when all sections empty so you know it ran
- Confirmed delivered to Telegram on first run

**AWS cron — morning alert scheduled:**
- scripts/run_morning_alert.sh: portable conda activation (same pattern as
  run_daily.sh), always sends
- Cron: 14:30 UTC (10:30 AM ET) weekdays
- Verified clean run on AWS — conda activation, Polygon snapshot, Telegram
  delivery all confirmed
- Two cron jobs now running: 14:30 UTC morning alert, 21:30 UTC daily pipeline
- Streamlit restarted after deploy — public dashboard serving HTTP 200 with the
  new tabs live

**Automation summary — full daily workflow now:**
- 10:30 AM ET: Telegram morning alert (live prices vs yesterday's levels)
- 4:30 PM ET: full pipeline + Telegram close alert with conviction scores

---

---

## Session 32 — June 10, 2026

**Built:** narrative_alert.py, fetch_earnings.py, holdings.yaml, moat_score.py
(commit 9099915 — built, tested, pushed, and deployed/verified on AWS the same day)

**narrative_alert.py — LLM plain-English daily briefing:**
- Runs after telegram_alert.py in run_daily.sh close pipeline
- Uses Claude API `claude-sonnet-4-6` — note: the roadmap's
  `claude-sonnet-4-20250514` is deprecated (retires June 15, 2026), so we used the
  current Sonnet instead
- Reads all signals: SPY/QQQ state, conviction ≥8 names, today's flips, high
  composite not yet up, 🗓️ earnings flags, holdings + dry-powder context, moat ratings
- Four sections: Market Context, Actionable Setups, Watch List, Bottom Line
- Plain English, no jargon, written for a long-term investor; sent as plain text
  (no Markdown) so LLM prose can't break Telegram's parser
- Graceful failure — logs error and skips if the API call fails; never breaks the
  pipeline (`|| true` in run_daily.sh too)
- Confirmed delivered to Telegram on first live test

**fetch_earnings.py — earnings calendar:**
- Source is **yfinance**, NOT Polygon — Polygon's forward earnings dates require
  the Benzinga add-on (not on this plan); yfinance is the free path to future dates
- 97 tickers, 74 with dates (ETFs correctly have none), stores data/earnings.parquet
- Built-in staleness guard (REFRESH_DAYS=6) — safe to call daily from run_daily.sh;
  only actually refetches when stale
- 🗓️ flag (≤7 days) surfaces in narrative_alert.py, morning_alert.py, daily_signals.py

**holdings.yaml — position context:**
- Simple weight snapshot: ticker → % weight, plus a CASH entry for money-market
  dry powder (no transaction tracking — broker handles that)
- Real positions loaded: NVDA 11, MSFT 11, AMZN 11, ELF 10, SOFI 8, PLTR 7, TSLA 7,
  META 7, AVGO 7, TSM 5, + CASH 16%
- Personalizes narrative ("you hold MSFT 11% — wide moat") and surfaces 💼 HELD in
  the dashboard Signals tab and morning alert; CASH is read as deployable dry powder

**moat_score.py — competitive moat scoring:**
- Claude API `claude-opus-4-8` (quality judgment, quarterly cadence justifies the
  better model; the daily narrative uses Sonnet), structured output per ticker
- Returns: moat rating 1-5, moat type, one-sentence summary, key risk
- 74 stocks scored (ETFs skipped via sector_map), stored in data/moat.parquet
  (dist: 12×5/5, 24×4/5, 15×3/5, 16×2/5, 7×1/5)
- Self-skips tickers scored within ~80 days — safe to re-run; run quarterly
- Surfaces in dashboard Fundamentals tab (rating + type + per-name detail panel),
  feeds moat context into narrative_alert.py
- Bug found & fixed mid-session: a dict/Series type-mix crashed the final parquet
  write after all 70 API calls succeeded — normalized to dicts and re-ran clean

**AWS deploy — fully verified (commit 9099915):**
- anthropic + yfinance installed in the AWS `stock` env (also pinned in requirements.txt)
- ANTHROPIC_API_KEY confirmed in AWS .env
- Full pipeline ran (135,631 rows in stock_vsa.parquet), earnings.parquet (97) and
  moat.parquet (74) generated on the server (data/ is gitignored)
- streamlit restarted; dashboard HTTP 200 externally at http://18.188.180.99:8501

**Automated daily workflow — now complete:**
- 10:30 AM ET: morning alert (live prices, 💼 held tags, 🗓️ earnings flags)
- 4:30 PM ET: close pipeline → signal alert → **narrative briefing** (new)
- Quarterly: `python moat_score.py` (manual, self-skipping)

---

## Session 33 — June 10, 2026

**Built:** dashboard narrative briefing — item A below (commit 82256f4 — built,
tested with Streamlit AppTest, pushed, and deployed/verified on AWS the same day).

**narrative_alert.py — refactored for reuse + persistence:**
- Extracted `generate_narrative()` (load signals → build context → call Claude,
  returns narrative + context), `save_briefing()`, `load_briefing()`
- `main()` now persists the briefing to `data/narrative_latest.json`
  ({date, generated_at, narrative}) on each real run, so the app shows it with
  zero per-view API cost. App and alert share the same functions — no forked logic.

**dashboard.py — 🧭 Briefing tab (now the first tab):**
- Renders the stored plain-English briefing with its as-of timestamp; the four CAPS
  section headers become h5s, "- " bullets render as a list
- **Read-only by design.** The dashboard is publicly reachable (no auth), so it
  must NOT expose any control that spends a Claude API call on our key. The
  on-demand "Regenerate" button I first built was removed at Spencer's call — the
  briefing is generated server-side by the trusted close cron and only displayed.
  (Saved as a standing rule: memory `public-dashboard-no-api-controls`.)
- Graceful empty state when no briefing exists yet (before the first close run).

**AWS deploy — verified (commit 82256f4):**
- git pull → 82256f4; briefing generated server-side (no Telegram) so the tab isn't
  empty; streamlit restarted; dashboard HTTP 200 local + external
- The 4:30 PM ET close cron now also refreshes the briefing the app displays

**Deferred to a future session (needs auth first):** on-demand regenerate and the
interactive Q&A (item B) — both spend API calls, so they're gated behind
authentication per the read-only rule above.

**Next session first task:** Review narrative alert quality after the first full
week of live runs — read the daily briefings, note where the read is off (tone,
missed context, over/under-caution), and tune the system prompt if needed.

---

## Session 34 — June 10, 2026

**Built:** universe management CLI, valuation layer, exit/trim framework, macro
calendar — the whole remaining roadmap (#2–#5). Each built, verified, pushed, and
deployed/verified on AWS the same day.

**#2 Universe management CLI (commit 2a819a4):**
- `universe.yaml` is now the single source of truth (ticker → sector ETF(s) +
  broad benchmark), generated from the old SECTOR_MAP (97 tickers, byte-identical).
- `universe.py`: load/tickers/write helpers. `sector_map.py` + `fetch_stock.py`
  (and `fetch_fundamentals.py`) now read it — no more hardcoded ticker lists.
- `manage_universe.py --add/--remove/--list`. Update-only by default (`--run` to
  fire the pipeline); `--remove` purges the ticker's parquet rows and warns if it's
  still in holdings.yaml. No core/watchlist tiers — "owned" is derived from
  holdings.yaml. Verified add→remove round-trip is byte-identical.

**#3 Valuation layer — PE / PEG / P-OCF (commits ca9f672, 60d06b0):**
- `valuation.py`: compute_valuation(price, row). **Context only, NOT in conviction**
  (Spencer's call). P-OCF stands in for P/FCF — Polygon financials don't expose capex.
- `fetch_fundamentals.py` stores TTM inputs (ttm_eps, ttm_ocf, shares,
  ttm_eps_growth); ratios computed against the live price so they refresh daily.
- Surfaced in narrative per-name tags + system prompt (premium ok for wide moats;
  flag stretched PEG) and in the dashboard Fundamentals tab.
- Data-quality fixes: Polygon returns ~1000×-wrong share counts for some quarters
  (AMZN/ELF) → use median diluted shares; guards drop implausible PE (<2) / P-OCF
  (<1) so bad data (e.g. BKNG's wrong price) can't surface garbage.

**#4 Exit/trim framework (commit 60d06b0):**
- `positions.py`: assess_position(zone, state) → TRIM (extended/above channel top),
  REVIEW (breakdown + Widell down), HOLD. Long-term framing, not hard stops.
- Narrative: YOUR POSITIONS review block + new **PORTFOLIO CHECK** section (5th).
- Morning alert: 💼 POSITION CHECK section flagging held names to trim/review.

**#5 Macro calendar (commit 9fce8b8):**
- `macro_calendar.yaml` (hand-maintained CPI + FOMC dates, seeded with the 2026
  schedule) + `macro_calendar.py`. Narrative gets an UPCOMING MACRO block + prompt
  guidance to treat fresh flips near CPI/Fed as noise — the Session 32 lesson, fixed.

**Known issue flagged (not fixed):** BKNG's price in the data is wrong (~$164 vs the
real ~$5,000) — a pre-existing upstream price-data artifact affecting all BKNG
signals, surfaced by valuation. Worth a separate look.

**Still open for a future session:**
- Review narrative quality after a full week of live runs (tune the prompt)
- Interactive Q&A on the app (item B) — **behind authentication** (memory
  `public-dashboard-no-api-controls`)
- Investigate the BKNG bad-price data issue

---

## Session 35 — June 10, 2026

**Built:** secular theme engine + TLT bond-regime signal, wired into the dashboard
and both alerts (commit deaa657 — built, tested, pushed, deployed/verified on AWS).

**Universe additions (Task 1):**
- `TLT` (20yr Treasury ETF) — a macro REGIME signal, not a position. TLT Widell up =
  yields falling = growth tailwind; down = headwind. Self-maps; auto-joined SECTOR_ETFS.
- `MP` (MP Materials — only US rare-earth producer at scale) → XLB / SPY.
- Pipeline re-run to 99 tickers; MP got fundamentals + moat; TLT skipped as ETF.

**themes.yaml (Task 2):** 10 human-curated secular themes + Bond_Market regime —
AI Infra, AI Software, Power Grid, US Reindustrialization, Defense, Critical
Materials, Materials/Industrial, Digital Finance, Space, Healthcare. Per theme:
thesis, conviction, constraint, names, best_in_class.

**theme_engine.py (Task 3):** `get_theme_status()` + `get_portfolio_theme_coverage()`.
Per theme: name-level status (state, conviction, zone, gap, fundamentals, moat,
valuation, entry status), best-in-class, held names, gap flag, best-entry-now. Plus
TLT regime, concentration, off-thesis holdings, and a **⭐ fits_profile** flag (wide
moat + reasonable valuation = Spencer's "wide moat × secular trend × cash-flowing
now" ideal). Self-contained loader (no narrative_alert import) to avoid a cycle.

**Dashboard 🌐 Themes tab (Task 4, 2nd tab):** TLT regime banner, coverage summary
(themes covered, positions vs 10-15 target, gaps, concentrated, off-thesis), and a
theme card per theme (conviction badge, thesis, best-in-class entry status,
HELD/GAP/⭐ badges, best-entry-now, constraint).

**Narrative (Task 5) + morning (Task 6):** narrative gets a THEME INTELLIGENCE
context block + prompt guidance (bond regime → MARKET CONTEXT; gaps → ACTIONABLE;
concentration/off-thesis → PORTFOLIO CHECK). Morning alert gets a TODAY'S THEME
OPPORTUNITIES section (best entry within 3% of pullback target; omitted when none).
All theme wiring is defensive — a theme error never breaks a briefing/alert.

**First live read it surfaced:** 3/10 themes covered, 7 gaps (incl. high-conviction
Power Grid + US Reindustrialization with zero exposure), AI Infrastructure
concentrated (NVDA/AVGO/TSM), and 4 off-thesis holdings (AMZN/ELF/META/TSLA).

**Follow-up (same session, commit edb5173):** reclassified the off-thesis names —
added a Physical_AI_Robotics theme (TSLA, AMZN, ISRG, SERV), put AMZN in
AI_Infrastructure + AI_Software, TSLA in Power_Grid. Off-thesis logic now carries an
optional per-ticker note (META annotated; ELF stays plain). Coverage 3/10 → 5/11;
only US Reindustrialization remains a high-conviction gap; off-thesis = ELF + META.

**Memory added:** `concentrated-conviction-investor`, `ideal-company-profile`.

**Documentation reframe — research platform → production decision-support system
(commit 6ceb1fd):** rewrote README (product-first; research moved to "How It Was
Built"), DECISIONS (vision-shift entry), renamed RESEARCH_ROADMAP → PRODUCT_ROADMAP
(Part 1 Research Arc / Part 2 active roadmap), reframed KEY_OBJECTIVES as the
canonical mission, added phase-orientation to this log, refreshed PROMPT.md. New
docs KEY_OBJECTIVES.md + MODEL_RISK.md, rendered in the dashboard Guide tab. Guide
tab walkthrough refreshed to cover all six tabs + the new signals (commit 4930645).

**Security: dashboard password gate (commit c63546e):** the public dashboard now
sits behind a password (DASHBOARD_PASSWORD in .env, constant-time compare,
fail-closed, session persistence). Verified on AWS: login screen with no holdings
leaked, wrong password → clear error, correct password → full app. Confirmed
working on mobile. Closes Model Risk #7 (public holdings exposure). Single password
sufficient for now; multi-user/guest mode queued for the Q&A era.

**#2 Position sizing engine (commits 916fcae, 6846492):** `position_sizing.py` —
conviction-led target weights. Rebalances held names (normalized across invested %,
cash held constant) → ADD/TRIM/HOLD vs current; plus gap starters (best-in-class in
high/medium-conviction uncovered themes). Score = conviction + theme + moat +
valuation + ⭐ fits-profile; caps at 15%, min starter 4%. New ⚖️ Sizing dashboard
tab + POSITION SIZING block in the narrative. Advisory only — never trades. First
read: add PLTR/META/AVGO, trim ELF (−8.9%)/SOFI/AMZN; gap starters CAT/CMI/ISRG/MP/FCX.

**Portfolio health check (commit 68bf704):** `portfolio_health.py` — one-glance
roll-up (position count, high-conviction gaps, theme coverage, concentration,
off-thesis, sizing drift, bond regime, dry powder) + overall grade; 🩺 cockpit panel
atop the Briefing tab. First read: "Needs attention" (1 red: US Reindustrialization
gap; 4 amber).

**Investment-thesis white paper (commit 00ca658):** `docs/INVESTMENT_THESIS.md` —
philosophy, macro thesis, the 11 secular themes, discipline, how the system
operationalizes the thesis, and what would change our mind. Rendered in the Guide tab.

**Conviction backtest (commit pending):** `backtest_conviction.py` +
`docs/CONVICTION_BACKTEST.md` — honest pressure test of the conviction score.
Conviction ≥8 single names: **+5.33% 20d SPY-relative alpha vs +2.77% rest (+2.55%
edge), +12.96% at 60d, win rate 58.6%, positive in EVERY year incl. the 2022 bear
(+8.46%)**. Honest limits: edge is a top-tier filter not a linear dial (Spearman
+0.026; 4-5 bucket trails 0-3 — likely beaten-down beta), and the absolute level is
inflated by the fundamental-component lookahead. Validates "conv ≥8 = highest
priority"; surfaced in the Guide tab. Re-run periodically.

**Still open for a future session:**
- Review narrative quality after a full week of live runs (tune the prompt)
- Interactive Q&A on the app — **behind authentication** (now unblocked by the password gate)
- Re-weight mid-scale conviction / remove fundamental lookahead (from backtest findings)
- Correlation awareness; spend-capped API key; HTTPS/TLS for the dashboard
- BKNG bad-price data investigation (~$164 vs real ~$5,000)

---

## Session 36 — June 11, 2026

**Built:** Portfolio-intelligence redesign — `holdings.yaml` is now the ONLY file
Spencer maintains; tier classification, theme mapping, 7% stop tracking, and cash
deployment are all DERIVED automatically (fresh at dashboard load + pipeline close).

**Design principle (the spine):** one hand-maintained file. New `holdings.yaml`
schema: `portfolio:` (total_value $1.3M, bi_weekly_contribution $1,600), `positions:`
(weights + CASH), `overrides:` (TSLA → core). Everything else computes from it.

**`holdings_io.py` (new):** single source of truth for reading holdings — positions /
cash / portfolio-meta / overrides, back-compatible with the old flat format. All six
prior `load_holdings()` copies + `position_sizing._load_cash` now delegate to it.

**`auto_classify.py` (new):** evidence-based CORE vs SPECULATIVE. CORE requires ALL of
moat≥4, fundamental≥4 (missing F doesn't block — international), high/medium theme,
weight>2%; else SPECULATIVE with the failing reasons spelled out. Overrides win.
Precedence resolves the deep-drawdown conflict: a core-quality name down ≥40% stays
CORE (buy-weakness, not a stop) — only non-core-eligible names are demoted by it.
First read: CORE = NVDA, MSFT, PLTR, AVGO, TSM, META, TSLA(override); SPEC = AMZN, ELF,
SOFI.

**`cash_deployment.py` (new):** "where does my next dollar go" — 4 priority steps
(add to core on weakness → high-conviction theme gap at entry → beaten-down quality →
hold cash with the trigger price). 7% stops tracked for SPECULATIVE only (core weakness
is a buy signal, never a stop), anchored on first-seen entry price in
`data/positions_seen.json` (system-maintained, gitignored). Thesis-integrity watches
core names for a ≥2-pt fundamental drop vs the last reading. First read: add
AVGO/NVDA/PLTR on weakness, ISRG beaten-down quality.

**Wiring:** Briefing tab's health cockpit replaced by a 🧠 Portfolio Intelligence
section (classification summary · next-dollar actions ≤3 · speculative stop watch ·
thesis alerts). Narrative gets a PORTFOLIO ACTION section + `record_positions()` at
close. Morning alert gets tier-aware open checks (speculative down >4% → stop watch;
core down >5% → potential add). Abandoned `table_setting.py` (the earlier deployment
sketch) deleted.

**Classification fixes (on evidence, not overrides):** META added to AI_Software theme
→ now CORE (was off-thesis). `fetch_fundamentals.py` EPS-growth criterion switched to
the stable TTM figure (was a noisy single quarter) — lifted AMZN 1→2, but confirmed
AMZN's low score is the software-tuned RUBRIC, not bad data (real blended margins
48.5%/11.7%, rev 13.6%). AMZN left SPECULATIVE pending the Session 37 fix.

**Verified:** 20/20 tests, both CLIs, dashboard AppTest clean. **Deployed to AWS**
(commit 8506d09) with Session 37 — see below.

**Next (Session 37) — sector-aware fundamental scoring:** one software-tuned rubric
mis-scores banks (JPM F=1 — no gross margin; ROE/efficiency), energy (cyclical), and
low-margin mega-caps (AMZN/COST). Polygon returns a full balance sheet + bank lines
(currently unused) → per-business-archetype 0-5 scoring on the right metrics. Fold in
the broader fundamentals pull + forward PE/PEG (yfinance) since a pull is needed anyway.
Re-scores all ~68 names → needs a full pipeline re-run. (memory `sector-aware-fundamentals`)

**Still open:** interactive Q&A (auth), BKNG bad-price data, narrative-quality tuning.

---

## Session 37 — June 11, 2026

**Built:** Sector-aware fundamental scoring + our own forward-PE projection — replaced
the single software-tuned rubric that mis-scored whole business categories.

**The problem:** one rubric (rev>20, gross>50, op>15, eps>10, +OCF) judged a bank, an
oil major, and a SaaS company by the same software thresholds. JPM scored F=1 (banks
have no gross margin), XOM/CVX F=1 (cyclical), AMZN F=1-2 (low blended margins by
design). Not bad data — the wrong yardstick.

**`business_model.py` (new):** each name gets a business archetype, then is graded by a
rubric that fits it (same 0-5 scale, so conviction + auto_classify are unchanged):
- Archetype from sector ETF (universe.yaml) + a small override list (AMZN/MELI→platform,
  TSLA→industrial, COST→staple). `pre_profit` is DATA-driven: non-positive TTM earnings
  AND non-positive operating cash flow (a GAAP loss alone doesn't qualify — cash-
  generative SaaS like CRWD/SNOW/ZS run GAAP losses from stock comp yet are real
  businesses, so they stay in software).
- Rubrics: software (current), platform (rev>10 / margin-expanding / ROE / FCF), financial
  (ROE / efficiency ratio / EPS growth / +NI), energy (ROE / FCF / low debt / +NI — not
  growth), industrial (op margin / ROE / FCF / trough-tolerant growth), staple (ROE /
  margin / FCF / dividend), consumer, pre_profit (path-to-profit, capped low).

**Comprehensive Polygon pull (`fetch_fundamentals.py`):** now extracts the full balance
sheet (equity, assets, long-term debt) + bank lines (noninterest_expense) — previously
discarded — and derives ROE, ROA, efficiency ratio, debt-to-equity, op-margin trend,
dividend flag. One pull, captured broadly.

**Our own forward projection (no analyst feed):** four YoY EPS readings (each recent
quarter vs the same quarter a year prior) → bear/base/bull growth band (min/median/max,
base=median). `valuation.compute_forward()` turns it into a forward PE band live against
price; forward PEG off base. Replaces the planned yfinance dependency — deterministic,
transparent, and the band itself communicates uncertainty (XOM's rising fwd PE flags
earnings decline; TSLA ~450 flags story-stock). Surfaced in the narrative valuation tag
and the dashboard Fundamentals tab (+ archetype column).

**Impact (on evidence, no overrides):** AMZN 1→5 (platform), JPM 1→4, XOM 1→3, CMI 1→4,
CAT→5, GOOG/META/NFLX→platform, HOOD→5. **AMZN is now CORE on its own merits** — the
classification reads 8 core / 2 speculative (only ELF + SOFI speculative, the genuinely
speculative names). Re-ran `conviction_score.py` to propagate F into conviction.

**Verified:** 20/20 tests, dashboard AppTest clean, full-book archetype/score review.

**Deployed to AWS (commit 8506d09):** git pull (fast-forward, no conflicts) →
regenerated `fundamentals.parquet` server-side with sector-aware scoring →
`conviction_score.py` re-run to propagate → streamlit restarted. Production smoke test:
8 core / 2 speculative, **AMZN CORE on the server**, cash-deployment engine live;
dashboard HTTP 200 externally. `positions_seen.json` will be created on the first close
run (record_positions); until then speculative stops anchor at the current price.

**Still open:** BKNG bad-price data, narrative-quality tuning, forward-PE for names with
<8 clean EPS quarters (NVDA post-split — graceful N/A for now).

---

## Session 38 — June 12, 2026

**Built:** Interactive Q&A on the dashboard — ask about any holding, candidate, or the
portfolio in plain English, answered from the same signal stack the alerts use.

**`qa_engine.py` (new):** `extract_tickers()` pulls universe tickers from a free-text
question (stopword-guarded so "NOW"/"IT" don't false-match); `build_qa_context()`
assembles the answer context by REUSING the existing builders — theme_engine
`_name_status` + `_load_signals`, `auto_classify` (tier + reasons), `valuation`
(incl. the forward-PE band), `cash_deployment` (per-ticker action/stop), moat detail,
and a portfolio snapshot (core/spec counts, cash, TLT regime). `answer_question()` calls
Claude (`claude-sonnet-4-6`) with a Q&A system prompt. **Signals only — no news feed**;
the prompt makes the model say so rather than inventing a catalyst. Honest, concise,
ends with a bottom line; core weakness framed as a buy, speculative stops respected.

**Dashboard 💬 Ask tab (2nd tab):** `st.chat_input` + history in session_state; each
answer shows the tickers it used as context. **API spend stays behind the password** —
`require_auth()` gates the whole app before the tab is reachable, satisfying the
standing rule (memory `public-dashboard-no-api-controls`, now unblocked by the Session 35
password gate). Guide tab updated; eight tabs total.

**Verified:** real Q&A answer validated end-to-end (AVGO "should I add?" → on-philosophy
read: core weakness = buy, forward-PE band, tranche entry, bottom line). 20/20 tests,
dashboard AppTest clean.

**Still open:** BKNG bad-price data, NVDA forward-PE (split-adjusted EPS), narrative-
quality review after a week, conviction mid-scale re-weight / remove fundamental lookahead,
optional Q&A news source (web search / news API) + multi-user guest mode.

---

## Session 39 — June 12, 2026

**Built:** Two related data-quality fixes — both stock-split / missing-quarter artifacts
in the Polygon feed.

**BKNG removed from the universe:** its price feed is persistently ~30× too low (stored
~$160, range $61–$232 over 1,506 bars; real BKNG ≈ $5,000) — a corrupt upstream price
series, so EVERY signal for it (Widell, conviction, channel) was garbage, not just
valuation. Non-thesis consumer name in no theme. `manage_universe.py --remove BKNG`
purged it from universe.yaml + all parquets (98 tickers now). Cleaner than reverse-
engineering a correction factor we can't trust.

**Forward growth made split-safe (fixes NVDA):** the forward-PE projection compared
quarters by POSITION (q_i vs q_{i+4}), which breaks across a stock split (post-split EPS
vs pre-split EPS) and across a missing quarter (Polygon gap). NVDA (10:1 split June 2024,
plus a missing Q4-FY2025) therefore fell out to N/A. Rewrote `fetch_fundamentals.py` to
match quarters by FISCAL PERIOD (Q1 vs Q1, year vs year-1) and measure growth on NET
INCOME, which is split-invariant (total $, not per-share). Now NVDA reads fwd PE 13.0
(9.8–19.2) from growth band 59–211%; MSFT a tight 19–21; META a wide band honestly
reflecting one weak quarter. The same fix hardened `ttm_eps_growth` (→ trailing PEG) and
`rev_growth_yoy` against splits for every name. Re-pulled fundamentals, re-ran conviction.

**Verified:** 20/20 tests, dashboard AppTest clean, NVDA forward-PE confirmed in the
narrative tag.

**Still open:** narrative-quality review after a week, conviction mid-scale re-weight /
remove fundamental lookahead, optional Q&A news source + multi-user guest mode.

---

## Session 40 — June 12, 2026

**Built:** Conviction score re-weight — backtest-driven, addresses the two flaws the
Session 35 backtest flagged (beaten-down-beta mid-scale + fundamental lookahead leverage).

**The diagnosis (empirical, `backtest_conviction.py`):** the old weighting rewarded
beaten-down names (channel `lower=4`, `breakdown=2`) and under-weighted the *validated*
Widell-state edge (only 0–2 of 10). So the mid-scale carried beta, not signal — the 0–3
bucket *beat* 4–5 and 6–7. Tested four candidate schemes on 100k+ bars of SPY-relative
forward alpha; the winner (scheme D) wins on Spearman, top-bucket edge, and year-by-year
persistence.

**New weighting (`conviction_score.py`):** Widell state **0–4** (up=4/inc=2/down=0 — the
validated edge becomes the top driver, so ≥8 now *requires confirmed up-momentum*),
channel **0–3** (middle=3/lower=3/upper=1/**breakdown=0**/**extended=0** — no reward for
broken structure), fundamentals **0–2** (down from 0–3 — less leverage on the only
lookahead-prone component), flip 0–1.

**Backtest result (vs the old scheme):** Spearman +0.0259 → **+0.0333**; win rate now
**monotonic** (52.5 → 56.9 → 56.8 → 61.2%); ≥8 edge +2.99% (20d), +12.3% (60d); ≥8
**positive every year incl. the 2022 bear at +13.72%** (was +8.46%). The 0–3 beaten-down
spike is gone. Honest limit unchanged: it's a top-tier filter, not a linear dial — the
mid-scale is coarse context.

**Downstream:** `cash_deployment.CORE_WEAK_CONV` 6 → 5 — under the new scale a down-state
core name in a good channel tops out ~5–6 (Widell "weakness" caps state pts), so 5 keeps
catching quality core pullbacks. `auto_classify` unchanged (doesn't use conviction). The
≥8 dashboard/narrative headline stays — in a weak tape it's correctly sparse/empty
("wait"), since high conviction now means up-momentum + good entry + quality.

**Verified:** 20/20 tests, dashboard AppTest clean, conviction range 0–10, classification
unchanged (8 core / 2 spec). Re-ran conviction; backtest doc rewritten with new numbers.

**Still open:** narrative-quality review after a week, optional Q&A news source +
multi-user guest mode, remove fundamental lookahead fully (needs point-in-time fundamentals).

---

## Session 41 — June 12, 2026

**Built:** Two Spencer-requested "keep-it-simple" features — a dashboard universe
manager and a lightweight investor diary.

**⚙️ Manage tab (dashboard):**
- **Universe** — Add (ticker + sector-ETF multiselect + SPY/QQQ) and Remove (dropdown)
  forms that call the existing `manage_universe.cmd_add/cmd_remove` (no forked logic).
  A new name backfills 6 years of data + signals at the next nightly close; a removal
  purges its parquet rows immediately. Round-trip verified byte-identical.
- **Investor diary** — `diary.py`: append-only `investor_diary.csv`, fixed schema
  (date, ticker, action, weight, recommendation, note). The Manage tab has a log form
  that **pre-fills from today's cash-deployment recommendations** (pick one → ticker +
  recommendation filled, you add the weight), a recent-entries table, and a Download
  button. The Briefing tab's next-dollar actions each get a **✅ Log** button that
  records "I acted on this" with the recommendation + today's date. The diary is the
  ACTION HISTORY; holdings.yaml stays the current-weight SNAPSHOT.

**State-sync reality (important):** AWS can't push to GitHub (HTTPS remote, no token),
so the planned "nightly cron commit+push" isn't available without a one-time PAT/deploy
key from Spencer. Pragmatic model adopted instead: the **diary is gitignored and
AWS-authoritative** (lives on the persistent instance; Download button for backup), and
**universe.yaml edits are reconciled with git at deploy time** (infrequent; handled
manually). Full GitHub auto-backup of these files stays an optional follow-up (needs the
token). No Claude-API spend in either feature, and both sit behind the password gate.

**Verified:** 20/20 tests, dashboard AppTest clean (9 tabs), diary log/load + universe
add/remove round-trip tested, `investor_diary.csv` confirmed gitignored.

**Still open:** narrative-quality review after a week; optional Q&A news source +
guest mode; optional GitHub auto-backup of universe/diary (one-time token); remove the
fundamental lookahead fully (needs point-in-time fundamentals).

---

## Session 42 — June 12, 2026

**Built:** Consolidated the recommendation surfaces — Spencer caught that the Briefing
had THREE overlapping, disagreeing action lists (the deterministic cockpit with Log
buttons showed only its top 3; the LLM narrative emitted its own ACTIONABLE SETUPS /
PORTFOLIO CHECK with different names + trims; only 3 items were loggable). Fixed by
making the engine the single source of truth.

**`cash_deployment` — one ranked, macro-aware action model:** every actionable item now
flows through one builder: **add-to-core, NEW SETUP (not-held on-thesis at conv≥8 —
best-in-class breadth across themes IS the thesis, Spencer's call, not dilution), gap
starter, TRIM/REVIEW (new — folds in `positions.assess_position`), beaten-down**. Each
gets a **priority rank** (conviction + theme conviction + ⭐fits-profile + entry quality)
and **NOW vs WAIT timing**: fresh buys WAIT (→ watchlist) when a CPI/FOMC is within 3
days (deterministic `macro_calendar` gate — so the engine agrees with the LLM's
"wait for the Fed") or the name is extended. Returns `actions` (NOW, ranked, loggable),
`watchlist` (WAIT items + conv 6-7 approaching), plus position-count/target context.

**Dashboard Briefing → two buckets:** 🎯 Portfolio Action (the one ranked NOW list,
every item ✅-loggable, type-iconed) + 👀 Watchlist, with a header showing positions vs
the 10-15 target + a macro-WAIT banner. **Narrative → context:** consolidated from six
sections to four (MARKET CONTEXT / PORTFOLIO ACTION / WATCHLIST / BOTTOM LINE); the
prompt now treats the engine block as the single source of truth and forbids a parallel
action list. `_BRIEF_HEADERS` updated (legacy headers still render).

**Verified:** 20/20 tests, dashboard AppTest clean, narrative context carries the
consolidated engine block. Engine output locally: 6 core adds + ISRG ranked NOW;
APP/GOOG/GLW (conv 6-7) on the watchlist (on AWS those are conv 8-9 → promote to NEW
SETUP actions).

**Still open:** narrative-quality review after a week; optional Q&A news source + guest
mode; optional GitHub auto-backup (token); remove fundamental lookahead fully.

---

## Session 43 — June 12, 2026

**Context:** Spencer added 5 names (DHR, ETN, PH, ROK, TMO) via the dashboard Manage
tab and wanted them refreshed NOW, not at the nightly close — which surfaced two
gaps: the EC2 box's memory fragility, and how much of "adding a name" was still
manual. Turned into a turn-key onboarding feature.

**🩹 Infra fix — EC2 was one memory spike from OOM.** The box has only **911 MB RAM
and no swap**; a manual `run_daily.sh` while Streamlit (~500 MB) was up got
`composite_score.py` **OOM-killed**. Added a **persistent 2 GB swapfile** (`/swapfile`,
in `/etc/fstab`) — fixes the manual run AND protects the nightly cron. The re-run
then completed clean; all 5 names backfilled (price/VSA/signals/conviction).

**⚙️ Turn-key universe onboarding (the session's main build):**
- **Theme selector in Manage → Add** — new `themes_io.py` (comment-preserving
  line edits to `themes.yaml`, NOT a yaml re-dump, so the hand-written thesis/
  constraint prose stays byte-identical; Bond_Market regime excluded). The Add form
  has a "Secular theme(s)" multiselect that writes the name into the chosen themes'
  `names:` lists; Remove unmaps it. No more hand-editing themes.yaml on the server.
- **Immediate full backfill — no gaps** — new `onboard.py`: adding a name now fires
  a **detached background job** that runs the exact nightly code paths
  (`run_daily.sh` → `fetch_fundamentals.py` → `conviction_score.py` →
  `moat_score.py`), so a new name is fully scored (price, signals, conviction,
  F-score, **moat**) in ~2-3 min instead of waiting for the nightly close +
  quarterly run. An **flock lock + rerun-flag** coalesces rapid successive adds into
  at most one extra pass (no overlapping full-universe rebuilds racing on the parquet
  writes). `moat_score.py`'s staleness guard means it only ever scores the NEW name
  (verified E2E on AWS: "79 in scope; 0 need scoring" — no mass re-score, no cost
  surprise). Telegram is never triggered (SEND_TELEGRAM unset), so onboarding is
  silent.
- This session's 5 names were also fully integrated by hand-running the same
  scripts: fundamentals (F 2-5), moat (all 4/5, wide-moat switching-costs), and
  theme assignments (Spencer-approved full mapping — DHR/TMO→Healthcare_Aging;
  ETN→Power_Grid+US_Reindustrialization+Materials_Industrial;
  PH→US_Reindustrialization+Materials_Industrial;
  ROK→US_Reindustrialization+Physical_AI_Robotics+Materials_Industrial).

**Verified:** 20/20 tests; dashboard AppTest clean both locally and on AWS (9 tabs,
"Secular theme(s)" selector present, no exceptions); themes_io add/remove round-trip
byte-identical + idempotent; onboard lock/coalesce logic unit-tested; onboard E2E ran
clean end-to-end on AWS. Local universe.yaml/themes.yaml reconciled to match AWS.

**Known wrinkle (follow-up):** healthcare/life-sciences-tools names under XLV
(DHR, TMO) get `archetype=software` in `business_model.py` and are mis-scored by the
software rubric (TMO landed F=2). Ties directly to the open `sector-aware-fundamentals`
item — these need a life-sciences/healthcare archetype + rubric. Industrials (XLI:
ROK/ETN/PH) scored correctly.

**Still open / next:** (1) **sector-aware fundamentals** — add a healthcare/
life-sciences-tools archetype so XLV names aren't graded as software (concrete,
surfaced today) — ✅ DONE in Session 44; (2) **GitHub auto-backup** of universe.yaml /
themes.yaml / diary — now THREE files drift on AWS via the dashboard (themes.yaml
joined the list this session); needs the one-time PAT/deploy key from Spencer;
(3) narrative-quality review after a week; (4) optional Q&A news source + guest mode;
(5) remove the fundamental lookahead fully (needs point-in-time fundamentals).

---

## Session 44 — June 12, 2026

**Built:** Closed the Session-43 follow-up #1 — the `healthcare` business archetype, so
XLV names stop being graded by the software rubric.

**The fix (`business_model.py`):** `XLV` now maps to a new `healthcare` archetype
(was `software`). New `_score_health` rubric grades medical-device / life-sciences /
pharma compounders on what actually signals quality for them — durable operating
margin (>15), a recurring cash engine (OCF>0), returns on capital (ROE>12), and
STEADY (not 20%+ SaaS) growth (eps>8, rev>5). Deliberately omits gross_margin:
Polygon often drops gross_profit for these names (TMO is NaN), so using it would
penalize on a data gap, not economics.

**Result (re-scored on AWS):** ISRG **5** (unchanged — genuinely fires on all
cylinders), TMO **2→4** (the bug — a quality compounder no longer punished for not
being hypergrowth), DHR **3** (fairly soft right now: slow growth + goodwill-depressed
ROE; its franchise quality shows via moat 4/5, and `fits_profile` keys off moat, so
DHR still flags). Biotech/pre-profit is still caught upstream by the `pre_profit`
archetype, so the new rubric only applies to profitable healthcare names.

**Verified:** rubric unit-tested against the 3 names' real fundamentals (5/4/3 as
intended); 20/20 tests; deployed to AWS, re-ran `fetch_fundamentals.py` +
`conviction_score.py`, restarted Streamlit (HTTP 200). Committed + pushed; AWS
reconciled to HEAD.

**Still open / next:** (1) **GitHub auto-backup** of universe.yaml / themes.yaml /
diary (3 files drift on AWS via the dashboard; needs a one-time PAT/deploy key);
(2) narrative-quality review after a week; (3) optional Q&A news source + guest mode;
(4) remove the fundamental lookahead fully. Possible further sector-aware tuning if a
new archetype surfaces (e.g. REITs/utilities) — none in the universe today.

---

## Session 45 — June 12, 2026

**Context:** First of the "observation & feedback" tweaks (Spencer flagged this as an
ongoing task — he'll surface UI issues as he sees them, not batched). He'd executed
real trades off the dashboard (trim SOFI/ELF to 3%, add AVGO to 15%, start
RTX/GOOG/GLW/DHR at 3%) and the log couldn't keep the allocations straight. Four
distinct bugs surfaced; all fixed.

**1. The log was ambiguous → records both halves of a trade.** The diary's single
free-text `weight` mixed conventions: the ✅ Log button wrote `suggested_pct` (a
DELTA — the add/trim amount), while hand entries were the new SIZE (a target). So
"AVGO 8%" (add amount, now at 15) and "SOFI 3%" (resulting size) couldn't be told
apart. Split into **`trade_pct`** (signed amount transacted) + **`new_weight`**
(resulting size); both captured every log. `diary.load_diary` is back-compatible and
migrates the legacy schema on first write (ADD's old weight → trade_pct, else →
new_weight).

**2. holdings.yaml went stale after every trade → logging now auto-syncs it.** New
**`holdings_io.apply_trade`** writes `new_weight` back into the positions block and
offsets CASH so the book still sums to 100 — comment/alignment-preserving LINE edits
(same discipline as `themes_io`), never a yaml re-dump. Both the Briefing Log buttons
and the manual diary form call it, so the snapshot Spencer hand-maintained now stays
current on its own (his stated long-term preference). This makes holdings.yaml a 4th
file that drifts on AWS via the dashboard — joins the GitHub-auto-backup follow-up.

**3. Two sizers disagreed (AVGO +8 vs +4.2) → one model.** Briefing "add to core"
filled to the 15% hard cap; the Sizing tab used `position_sizing`'s conviction-led
target. `cash_deployment` now sizes add-to-core off that same target (skips when
already at/above it), so Briefing and Sizing agree by construction. Each action item
carries `held_pct` + `new_weight` for the log/holdings write.

**4. Fresh adds were stranded → a loggable Validations bucket.** Names the narrative
raised but the conv-8 action line filtered out (DHR — soft-scored healthcare he'd
acted on from the Morning Alert) had no Log button. New **🧪 Validations** section
surfaces not-held, on-thesis, `fits_profile` (wide moat + fair/cheap) names below the
action line, each loggable. Keyed on moat so quality compounders aren't dropped for
lacking momentum.

**Reconciled + deployed:** holdings.yaml set to the real post-trade book (SOFI/ELF 3,
AVGO 15, +RTX/GOOG/GLW/DHR 3, CASH 8). The 7 AWS diary rows were rewritten to the
2-field schema with accurate trade/new values (notes preserved; original backed up to
`investor_diary.csv.bak.s45`). Pushed to git (source of record), pulled on AWS,
diary uploaded, Streamlit restarted.

**Verified:** 27/27 tests (+7: apply_trade add/trim/insert/full-exit/comment-preserve
+ diary schema/migration); dashboard AppTest clean locally AND on AWS (0 exceptions,
HTTP 200). On AWS post-deploy: CASH 8%, add-to-core emits conviction-led deltas
(RTX/GOOG +6→9, etc.), AVGO correctly dropped (at cap), DHR moved candidate→holding so
the Validations bucket self-updated to ETN. Diary reads 7 rows on the new schema.

**Still open / next:** (1) **GitHub auto-backup** — now FOUR files drift on AWS
(universe / themes / diary / **holdings.yaml**); needs the one-time PAT/deploy key;
(2) narrative-quality review after a week; (3) optional Q&A news source + guest mode;
(4) remove the fundamental lookahead fully. Feedback loop is now an explicit ongoing
task — expect more small UI/logic tweaks like this one.

---

## Session 46 — June 12, 2026

**Context:** Second observation-and-feedback tweak (same-day). Spencer used the live
build — confirmed the streamlined log works and he's now catching **mid-day**
Briefing recommendations (he logged a trim AVGO 15→11 and a starter ETN 3% via the
dashboard, both of which auto-synced to holdings.yaml — the Manage→holdings loop
verified end-to-end in production). His feedback: **consolidate ALL recommendations
on the Briefing; the Sizing tab should not advise.**

**The bug he hit:** the Sizing tab's rebalance table compared each holding to a
conviction-NORMALIZED target (targets sum to invested%). After he deployed cash, his
big CORE names sat above their normalized share, so every one showed "→ TRIM" —
including cheap, high-conviction NVDA. Noise, and mixed messaging vs the Briefing.

**Fix — Sizing tab is now read-only/informational:**
- Rebalance table → "Your positions — weight vs max": ticker, current %, max %
  (the 15% single-name cap), **room %** (cap − current), conviction, moat, val, ⭐.
  Dropped the target / Δ / ADD-TRIM-HOLD columns. Sorted by weight.
- **Removed the "Starters" section entirely** — starter recommendations belong on the
  Briefing (NEW SETUP / 🧪 Validations). Captions now point to the Briefing to act.
- The Briefing was never the source of the spurious trims (its TRIM/REVIEW step is
  technical/extended-only via `positions.assess_position` — verified: zero core trims
  on the reconciled book; one legit ELF technical trim). `position_sizing` still
  computes targets for the Briefing's add-to-core sizing; only the Sizing *UI* stops
  advising. Net: one place to act, and Themes/Sizing are pure opportunity/context
  surfaces (Spencer explicitly likes Themes for exactly this reason).

**Also:** `_log_and_apply` now auto-signs `trade_pct` from the action (TRIM/SELL
negative, BUY/ADD positive) so a trim typed "4" logs "-4". Guide gained a Sizing row
("no actions here") and a note that Themes lists opportunities, not directives.

**Reconciled + deployed:** holdings.yaml brought to the live book (AVGO 11, +ETN 3,
CASH 9) — git is the record (AWS dashboard-write was byte-identical to the pushed
commit, so the sync clobbered nothing). Pushed, pulled on AWS, `systemctl restart
streamlit`, HTTP 200.

**Verified:** 27/27 tests; dashboard AppTest clean locally AND on AWS (0 exceptions);
Briefing core-trim check = none spurious; holdings intact post-deploy.

**Still open / next:** unchanged — (1) **GitHub auto-backup** of the 4 drifting files
(the one-time PAT is the gating item, getting more valuable each tweak); (2) narrative
review after a week; (3) Q&A news/guest mode; (4) remove fundamental lookahead.

---

## Session 47 — June 12, 2026

**Context:** Spencer's first STRATEGIC feedback (vs point fixes). Strengths to keep:
useful framework, simple UI, LLM-interactive, phone alerts, actionable, disciplined.
Weaknesses all point one way: **make me more concentrated and decisive, not give me a
longer menu** — too many actionable choices, would run out of cash, want positions to
COMPLETE and add to winners, be decisive (non-core → sell not trim, drop overrides,
"let the system work"). He picked **Concentrate & Complete** to build first, and
confirmed **sell non-core + drop overrides** (incl. TSLA).

**New `destination.py` — the Destination Book + cash-aware Next Steps:**
- **Destination Book** = the portfolio he's building toward: held CORE names get a
  conviction-led target (water-fill to 100−reserve, cap 15%, **8% cash reserve**).
  Override-free classification.
- **Decisive buckets:** a held non-core name that's low-quality (moat≤2 & fund≤2) OR
  off-thesis (no theme) → **SELL** (full exit, not a trim-to-rump); one that still has
  an edge → **SPEC sleeve** under the −7% stop; just-onboarded/unscored → **PENDING**
  (untouched). On his book: SELL = ELF (off-thesis, low-Q) + SOFI (low-Q) — exactly
  the two he'd flagged.
- **Cash-aware queue:** sells + reduces free cash → COMPLETE the underweight winners,
  ranked, walking the deployable pool (partial-fills the marginal name, waitlists the
  rest). REDUCE fires **only** when overweight AND low-conviction (e.g. MSFT conv 3) —
  never nags a trim on a high-conviction winner (Spencer's "leave winners alone" call).
  The elegance: selling the 2 losers funds completing the winners, landing at reserve.

**Wiring:**
- Dropped the TSLA→core override (`holdings.yaml` overrides now intentionally empty,
  with a comment); TSLA classifies on evidence → spec sleeve + stop.
- Briefing cockpit is now **destination-driven**: one 🎯 Next Steps queue (Log +
  holdings auto-sync), spec sleeve, "when cash frees up", new ideas demoted behind an
  expander until the book is complete. Stops/thesis/watchlist kept as context.
- Sizing tab → **⚖️ Destination**: the current→target book map + spec/exit/pending
  buckets. Still read-only; the Briefing is the only place to act.

**⚠️ Deploy incident (caught + fixed):** the AWS reconcile used
`git diff origin/main … && echo MATCH` — but plain `git diff` returns 0 even WITH
differences, so "MATCH" was a false positive and `git checkout -- holdings.yaml`
**clobbered a live PLTR 7→8 trade** Spencer had logged on AWS. Caught via the
append-only diary (the trade was recorded there), restored PLTR→8 / CASH→8, re-pushed.
**Lesson (now in aws-deploy-gotchas):** before any reconcile/checkout, check AWS drift
with `git diff --quiet` (exit code) and cross-check the diary; never blind-checkout
holdings.yaml — it's dashboard-written and AWS is often the newer truth.

**Verified:** 33/33 tests (+6 destination invariants: sells are full exits & non-core,
targets ≤ cap, pool = cash+sells+reduces, adds ≤ deployable); AppTest clean locally and
on AWS (0 exceptions); live engine on AWS sells ELF/SOFI, completes GOOG, waitlists
RTX/ETN, TSLA in the spec sleeve. Deployed (b6a832a), HTTP 200.

**Still open / next:** the rest of the strategic roadmap — (a) **Tide overlay**
(Rotation → regime dial that scales deployment, "don't fight the tide"); (b) **editable
holdings** on Manage (safety valve for a mis-synced weight); (c) **Idea of the Day**
(single daily highest-conviction insight to phone); (d) de-emphasize the raw Signals
tab (the action+detail carries the meaning); (e) narrative_alert should consume the
destination queue so the LLM read matches. Plus the standing **GitHub auto-backup**
token (now even more valuable — would have prevented the clobber).

---

**B. Interactive Q&A on the app** *(DONE — Session 38)*
- Free-text box: "thoughts on GEV today?" / "any news on X?" — pass that ticker's
  full signal row + theme as context, same builders the alerts use
- News needs a source (Claude web search/fetch, or a news API) — scope signals-only first
- **Must be behind auth** (memory `public-dashboard-no-api-controls`) — the public
  dashboard never exposes a control that spends our API key

### Design principles for all new features
- Holdings file is a weight snapshot, not a trade tracker; universe + themes are
  single-source YAMLs (manage_universe.py / hand-edited)
- Moat and valuation run quarterly; themes are hand-curated, not a daily input
- The app is an insight + interaction surface — narrative/themes/Q&A reuse the same
  context builders the alerts use (don't fork the logic)
- No Claude-API-spending controls on the public (no-auth) dashboard until auth exists

---

## Session start checklist
- [ ] Open Ubuntu app
- [ ] `cd ~/projects/stock-pipeline`
- [ ] `./scripts/morning_startup.sh`
- [ ] `conda activate stock`
- [ ] `./scripts/run_checks.sh`
- [ ] `python daily_signals.py`
- [ ] `python sector_rotation.py`
- [ ] Check http://18.188.180.99:8501
