# Product Roadmap

> *Empirical rigor earned the foundations. The system now exists to turn those
> foundations into clear, honest, plain-English decisions for a specific investing
> philosophy: wide moats, secular trends toward the future, cash-flowing now, held
> in a concentrated portfolio of 10 best-in-class names.*

This document has two parts. **Part 1** is the completed research arc — the origin
story that validated the signal stack. **Part 2** is the active product roadmap —
what the system is becoming now that research is done.

---

# Part 1 — Research Arc (Completed)

The empirical journey from a VSA hypothesis to a validated signal stack. This phase
is **done**; it earned the foundations the product now builds on.

## The question

Most market frameworks are built on tradition and intuition. The research asked:
do **Volume Spread Analysis** and **Wyckoff** principles contain *measurable*
predictive signal — and if so, can it be quantified and used systematically? Every
claim was treated as a hypothesis: start with the simplest deterministic rule,
measure it across real data and regimes, add complexity only when simpler models
fail.

## What it produced

- **The Widell Line** — an original swing-structure state machine (resistance/
  support via a confirmed-optimal N=3 window → up / inconclusive / down). Clean
  state separation validated across 6 years and 3 market segments (up +2.38%,
  inconclusive +0.95%, down −0.83% over 5 days; spread scales with volatility:
  tech 3.21%, value 1.61%, market 0.98%).
- **VSA chapter closed** — six deterministic bar types showed no consistent
  standalone signal (last in ML importance, 0.08%). VSA was the scaffolding that
  led to the Widell Line.
- **Composite score (−6..+6)** — works as a filter at the extremes (≥2 reliably
  positive; middle zone is noise), not a trade-by-trade classifier.
- **ML ceiling found** — Random Forest / XGBoost / Optuna / LSTM all cluster at
  0.408–0.417 on SPY-relative alpha (naive 0.368). The Widell Line ranks 1st/2nd
  among non-momentum features. The edge is the *interpreted signal stack*, not a
  black-box predictor — so the product builds on the signals, not a higher AUC.
- **The 2022 lesson** — a headline +11.53% combined signal turned out to be entirely
  2022 bear-market snapbacks. Every result is broken down by year and regime. This
  discipline carries into production (flips in weak tape / around macro = noise).

## Research session arc (Sessions 1–21)

- Sessions 1–6: Infrastructure — WSL, conda, Git, Parquet, DuckDB, shell automation
- Sessions 7–8: VSA features and bar classification
- Sessions 9–10: Dataset expansion, hypothesis testing, regime classifier
- Session 11: Widell Line — swing state machine, N=3 validated
- Sessions 12–14: 2022 artifact lesson, universe expansion, cross-segment validation
- Session 15: Composite signal scoring
- Sessions 16–20: ML layer — RF → XGBoost → Optuna → LSTM; ceiling confirmed
- Session 21: run_checks.sh, daily_signals.py — the bridge to production

## Guiding research principles (still in force as engineering values)

1. Learn from first principles — every claim is a hypothesis
2. Deterministic before probabilistic; interpretable before complex
3. Infrastructure before analysis — reproducibility is prerequisite
4. Regime first — no signal evaluated without regime context
5. Stress-test headlines — year-by-year breakdown is mandatory

---

# Part 2 — Product Roadmap (Active)

Research is the means; the product is the end. The mission is to interpret the
validated stack into plain-English decisions for a concentrated conviction investor.

## ✅ Completed (production)

- **Conviction scoring (0–10)** — buy-zone quality: channel + fundamentals + Widell
  state + flip recency (Session 30)
- **Fundamental score (0–5)** + **valuation layer** (PE / PEG / P-OCF, context only)
- **Moat scoring (1–5)** via Claude, quarterly
- **Narrative briefing** — daily plain-English LLM read (market context, actionable
  setups, watch list, portfolio check, bottom line), on Telegram and the dashboard
- **Theme engine** — secular-trend map (11 themes), coverage / gaps / concentration
  / off-thesis / best-entry-now, with the ⭐ "wide moat × secular × cash-flowing"
  profile flag
- **Macro calendar** — CPI/FOMC proximity + **TLT bond-market regime** as narrative context
- **Holdings personalization** — holdings.yaml weights + CASH dry powder
- **Exit/trim framework** — TRIM / REVIEW / HOLD status per held name
- **Universe management CLI** — `universe.yaml` single source of truth + earnings flags
- **Three daily Telegram alerts + six-tab dashboard**, deployed on AWS
- **Dashboard password gate** — whole app behind a password (holdings private);
  closes Model Risk #7's dashboard-exposure concern (Session 35)
- **Position sizing engine** — conviction-led target weights: rebalance held names
  (ADD/TRIM/HOLD vs current, cash held constant) + gap starters; ⚖️ Sizing tab +
  narrative. Advisory only (Session 35)
- **Portfolio health check** — one-glance roll-up (position count, high-conviction
  gaps, coverage, concentration, off-thesis, sizing drift, bond regime, dry powder)
  + overall grade; 🩺 cockpit panel atop the Briefing tab (Session 35)
- **Investment-thesis white paper** — `docs/INVESTMENT_THESIS.md`, rendered in the
  Guide tab (Session 35)
- **Conviction backtest** — `backtest_conviction.py` + `docs/CONVICTION_BACKTEST.md`:
  conviction ≥8 validated (+2.5% 20d alpha, positive every year incl. 2022 bear);
  honest limits noted (top-tier filter, fundamental lookahead) (Session 35)

- **Portfolio-intelligence redesign** — `holdings.yaml` is the only file maintained
  by hand; CORE/SPECULATIVE tier, theme mapping, 7% stops (speculative only), and
  cash deployment are all derived fresh. `holdings_io.py` + `auto_classify.py` +
  `cash_deployment.py`; 🧠 Briefing cockpit, narrative PORTFOLIO ACTION, tier-aware
  morning checks. Advisory only (Session 36)

- **Sector-aware fundamental scoring (Session 37)** — `business_model.py`:
  per-business-archetype 0-5 rubrics (software / platform / bank / energy / industrial /
  staple / pre-profit), each on the metrics that fit (ROE, efficiency ratio, FCF), using
  the full Polygon balance sheet. `pre_profit` is data-driven (no earnings AND no cash).
  Fixed AMZN/JPM/XOM/CMI on evidence — AMZN now CORE without an override.
- **Forward PE/PEG — our own run-rate projection** — bear/base/bull EPS-growth band from
  four historical YoY readings (no analyst feed); `valuation.compute_forward()`. In the
  narrative tag + Fundamentals tab. Deterministic and honest about uncertainty.

- **Interactive Q&A on the dashboard (Session 38)** — `qa_engine.py` + 💬 Ask tab:
  ask about any holding/candidate/the portfolio in plain English, answered from the
  same signal stack the alerts use (reuses theme_engine / auto_classify / valuation /
  cash_deployment). Signals only (no news feed). API spend behind the password gate.
- **Data-quality fixes (Session 39)** — removed BKNG (corrupt ~30× price feed, no
  clean correction); made forward growth split-safe via fiscal-period-matched net
  income (split-invariant), fixing NVDA's forward PE and hardening trailing PEG /
  rev-growth for every name across splits + missing quarters.

- **Turn-key universe onboarding (Sessions 41, 43)** — ⚙️ Manage tab: add/remove a
  company (`manage_universe.py`), pick its secular theme(s) (`themes_io.py`,
  comment-preserving), and fire an **immediate full backfill** (`onboard.py`: price /
  signals / fundamentals / conviction / moat in ~2-3 min, flock-coalesced). No
  hand-editing YAML on the server.

- **Investor diary that keeps the book current (Sessions 41, 45)** — `diary.py`: an
  append-only action log recording each trade as a **signed amount (`trade_pct`) AND the
  resulting weight (`new_weight`)**. Logging writes the new weight straight back into
  `holdings.yaml` via `holdings_io.apply_trade` (CASH offsets so the book stays at 100%),
  so the snapshot never drifts. ✅ Log buttons on the Briefing; gitignored + AWS-authoritative.

- **One recommendation surface (Sessions 42, 46)** — every actionable item flows through
  ONE engine and shows up in ONE place: the Briefing. Sizing / Themes / Tide are
  read-only context, not parallel action lists. (Fixed the "three disagreeing action
  lists" and the "every core says trim" noise.)

- **Sector-aware healthcare archetype (Session 44)** — `business_model.py`: XLV names
  (TMO/DHR/ISRG) graded on durable margins / recurring cash / ROE / steady growth, not
  the SaaS rubric.

- **The Destination Book — concentrate & complete (Session 47)** — `destination.py`: the
  portfolio you're *building toward* — held CORE names at conviction-led targets
  (water-fill to 100−reserve, cap 15%). One cash-aware queue: **decisive SELL** of a
  non-core low-quality/off-thesis name (full exit, not a trim), proceeds **complete the
  underweight winners**, **REDUCE** only on overweight-AND-low-conviction. Walks the
  deployable cash (funds now / waitlists the rest). **No manual overrides** — a name
  earns CORE on the evidence or sits in the speculative sleeve under the −7% stop.

- **The Tide — top-down regime pacing (Session 48)** — `tide.py`: a market regime
  (rising/neutral/falling) fused from the benchmarks + sector breadth + TLT. It paces
  deployment (the cash reserve: 5/8/12%) and, in a falling tide, defers adds whose sector
  is sinking — *don't fight the tide*. Changes the pace, never the destination. The old
  Rotation tab became the 🌊 Tide tab.

- **Editable holdings on Manage (Session 49)** — `holdings_io.write_positions`: an
  editable weights table on the Manage tab; CASH auto-recomputes; a 0 drops a name.
  A correction safety valve (not a logged trade) for a mis-synced weight.

- **Idea of the Day (Session 50)** — `idea_of_the_day.py`: ONE synthesized insight per
  day, picked by a priority ladder (stop hit → thesis break → tide turn → top step →
  patience), framed by the tide. A 💡 card atop the Briefing + a 10:30 AM phone push
  (rides the morning cron, which also records the day's tide). Deterministic, no API cost.

- **One voice — the narrative consumes the new model (Session 51)** — `narrative_alert.py`
  now feeds Claude the SAME engines as the cockpit (the Tide, the Idea of the Day, the
  Destination Book + cash-aware Next Steps) and the prompt speaks the decisive,
  concentrate-&-complete, tide-aware language. The close briefing and the cockpit agree
  exactly. Sections: MARKET & TIDE / NEXT STEPS / WATCHLIST / BOTTOM LINE.

- **Decision-first tabs (Session 52)** — reordered so the meaning surfaces lead
  (Briefing · Destination · Tide · Themes · Ask · Fundamentals · …) and the raw stack
  ("📊 Signals (raw)") sits near the back as reference, not a daily read.

## 🚧 In progress

- *(open — the Session-47 strategic arc is complete; next is observation-and-feedback
  from live use, or the GitHub backup token below)*

## 🔜 Upcoming
- **GitHub auto-backup** — four dashboard-written files drift on AWS (universe / themes /
  diary / **holdings.yaml**); a one-time PAT/deploy key lets the box back itself up to git
  (would also have prevented the Session-47 holdings clobber). The gating item is the
  token from Spencer.
- **Multi-user auth / guest mode** — read-only access without holdings visibility.
- **Correlation awareness** — flag when "diversification" across themes is really the
  same underlying bet (e.g. everything long-duration growth).

## Design principles for the product

- `holdings.yaml` is the one hand-maintained file — but logging a trade now keeps it in
  sync automatically; everything else (tier, stops, targets, tide, deployment) is derived.
- **One place to act (the Briefing); every other tab is read-only context** — no
  parallel or disagreeing action lists.
- **Be decisive** — core is held/completed through volatility; non-core is a full exit,
  not a trim; speculative lives under a stop; no manual overrides. Let the system work.
- The Tide paces the plan; it never moves the destination (so the book doesn't churn).
- Moat and valuation run quarterly; themes are hand-curated — not daily overhead.
- Reuse the same context builders across narrative / themes / Q&A — don't fork the logic.
- No Claude-API-spending controls on the public (no-auth) dashboard until auth exists.
- The system advises; it never trades — human-in-the-loop is the ultimate control.

---

*Living document. Part 1 closed at Session 21; Part 2 active from Session 22 onward.*
