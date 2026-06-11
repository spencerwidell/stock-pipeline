# Session Log — Stock Pipeline Project

**Phase orientation (read first):**
- **Sessions 1–21:** Research and validation phase — earning the foundations.
- **Sessions 22+:** Production system development — turning signals into a live product.
- **Sessions 35+:** Decision-support system evolution — interpreting the stack into
  plain-English decisions for a concentrated conviction investor (see
  `docs/KEY_OBJECTIVES.md`).

For sessions 1-24 see docs/SESSION_ARCHIVE.md

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

**Still open for a future session:**
- Review narrative quality after a full week of live runs (tune the prompt)
- Interactive Q&A on the app (item B) — **behind authentication**
- BKNG bad-price data investigation (~$164 vs real ~$5,000)
- Off-thesis reclassification DONE (commit edb5173); ELF + META remain intentionally off-thesis
- Position sizing engine (Session 36 main build)

---

## Session 36 — (upcoming)

First task: review narrative quality after a week of live runs. Then item B
(interactive Q&A, behind auth), the BKNG price-data fix, and deciding whether the
off-thesis holdings belong in a theme.

**B. Interactive Q&A on the app** *(Medium effort)*
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
