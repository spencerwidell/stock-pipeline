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

## 🚧 In progress

- *(open — pick the next build)*

## 🔜 Upcoming

- **Interactive Q&A (auth-gated)** — "thoughts on GEV today? any news?" in the app,
  behind authentication (no API-spending control on the public dashboard until then)
- **Multi-user auth / guest mode** — read-only access without holdings visibility,
  for when interactive Q&A ships (the current single password is sufficient until then)
- **Security hardening (remaining)** — spend-capped API key, HTTPS/TLS, and an
  optional IP allowlist. Dashboard auth is DONE (password gate, Session 35).
- **Correlation awareness** — flag when "diversification" across themes is really the
  same underlying bet (e.g. everything long-duration growth)

## Design principles for the product

- Holdings is a weight snapshot, not a trade tracker; universe & themes are
  single-source YAMLs
- Moat and valuation run quarterly; themes are hand-curated — not daily overhead
- The app is an insight + interaction surface; narrative/themes/Q&A reuse the same
  context builders the alerts use (don't fork the logic)
- No Claude-API-spending controls on the public (no-auth) dashboard until auth exists
- The system advises; it never trades — human-in-the-loop is the ultimate control

---

*Living document. Part 1 closed at Session 21; Part 2 active from Session 22 onward.*
