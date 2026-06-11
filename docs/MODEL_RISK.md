# Model Risk Monitoring

A living register of the things that can make this system **wrong, stale, or
misleading**, what we do about each, and how we'd notice. Reviewed at the start of
each session and whenever a new data source or model is added.

This is a decision-support tool for one investor — it never places trades — so the
ultimate control is **human-in-the-loop**: every output is advisory and Spencer
makes the call. That backstop is assumed throughout.

## Risk register (summary)

| # | Risk | Severity | Likelihood | Mitigation status |
|---|------|----------|-----------|-------------------|
| 1 | Bad market data (wrong price/shares) | High | Medium | Partial — guards + median shares; BKNG open |
| 2 | Single data vendor (Polygon) | Medium | Low | Accepted; yfinance for earnings only |
| 3 | Signal heuristics not statistically validated | Medium | High | Accepted by design; advisory only |
| 4 | LLM hallucination (narrative / moat) | Medium | Medium | Structured context, plain-text, human review |
| 5 | Valuation proxy error (P-OCF, PEG) | Low | Medium | Labeled proxy + sanity guards |
| 6 | Stale hand-maintained inputs (macro, themes, holdings) | Medium | Medium | Source links; surfaced freshness |
| 7 | Public dashboard exposes holdings (no auth) | Medium | High | Open — recommend auth/IP allowlist |
| 8 | Deployment/data drift (data/ gitignored) | Medium | Medium | Documented runbook; regenerate on deploy |
| 9 | Model/API deprecation & cost | Low | Medium | Pinned current models; fail-soft |
| 10 | Behavioral: over-trust / over-concentration | Medium | Medium | Theme concentration flags; honest tone |

---

## 1. Data quality
**Concern.** Vendor data can be wrong: BKNG currently prices at ~$164 vs a real
~$5,000 (a Polygon adjustment/split artifact), and Polygon returns ~1000×-wrong
`diluted_average_shares` for some quarters (AMZN/ELF). Garbage price/shares flow
into channel position, gap-from-flip, and valuation.
**Mitigation.** Valuation uses **median shares** over recent quarters; valuation
ratios are **sanity-guarded** (PE < 2 or P-OCF < 1 dropped). 20-test pytest suite
guards pipeline regressions.
**Monitoring.** Watch for implausible PE/P-OCF in the Fundamentals tab; spot-check
new tickers after `--add`.
**Open.** BKNG bad price affects *all* its signals, not just valuation — needs an
upstream price-sanity check (flag tickers whose price moved >50% vs prior bar
without a known split). Tracked for a future session.

## 2. Data-vendor concentration
**Concern.** Prices, fundamentals, and snapshots all come from Polygon; earnings
from yfinance. A vendor outage or schema change breaks a layer.
**Mitigation.** Each fetch is fail-soft and isolated; earnings/fundamentals/moat
are optional enrichments the core pipeline degrades without. yfinance is used only
for forward earnings (low blast radius).
**Status.** Accepted for a personal project; revisit if reliability degrades.

## 3. Signal validity (Widell Line, conviction, channel)
**Concern.** The Widell Line is a **heuristic state machine**, conviction (0–10)
and composite are **judgment-weighted blends**, and the regression channel assumes
mean-reversion. None are calibrated probabilities; ML work (Sessions 18–20) capped
predictive edge at ~0.417 AUC-equivalent. Weights are not optimized and could
overfit the current regime.
**Mitigation.** Outputs are explicitly **advisory and confirmatory**, never
predictive guarantees; the narrative is instructed to treat flips in weak tape /
around macro as noise. Conviction is a *buy-zone-quality* metric, not an expected
return.
**Monitoring.** Session 36+ "narrative quality review" after a week of live runs;
periodically sanity-check that high-conviction calls behaved sensibly.

## 4. LLM risk (narrative briefing, moat scores)
**Concern.** Claude can hallucinate or over/under-state. The narrative could
misread the data; moat ratings (1–5) are **subjective LLM opinions**, point-in-time,
and may carry training bias.
**Mitigation.** The narrative is given **structured, factual context** and asked to
interpret only what's provided; sent as plain text. Moat scoring uses structured
output and runs quarterly (low frequency, human-reviewable in the dashboard).
Failures are caught — a bad/failed API call logs and skips, never breaks the
pipeline. Model pinned to a current ID (`claude-sonnet-4-6` narrative,
`claude-opus-4-8` moat).
**Monitoring.** Read the daily briefing critically; moat scores visible per-name in
the Fundamentals tab for sanity. Re-tune the system prompt as drift appears.

## 5. Valuation proxy error
**Concern.** **P-OCF stands in for P/FCF** (Polygon doesn't expose capex), and PEG
uses TTM EPS growth that can be noisy or missing. Labeled thresholds are heuristic.
**Mitigation.** P-OCF is **explicitly labeled a proxy** in the narrative and docs;
valuation is **context only, not part of conviction** (Session 34 decision); sanity
guards drop implausible values.
**Status.** Acceptable as directional context.

## 6. Stale hand-maintained inputs
**Concern.** `macro_calendar.yaml` (CPI/FOMC), `themes.yaml` (trend map), and
`holdings.yaml` (positions) are **hand-maintained**. A stale macro calendar yields a
false "no events"; stale holdings mis-personalize; stale themes misclassify.
**Mitigation.** Each file carries maintenance source links; the dashboard surfaces
holdings and theme coverage so staleness is visible. Macro events show "today /
in Nd / Nd ago" so an empty window is obvious.
**Monitoring.** Refresh macro dates each quarter from the Fed/BLS schedules; update
holdings after meaningful trades.

## 7. Public dashboard exposes holdings
**Concern.** `http://18.188.180.99:8501` is **publicly reachable with no auth** and
displays actual holdings and weights — an information-disclosure risk.
**Mitigation today.** No Claude-API-spending controls are exposed (see memory
`public-dashboard-no-api-controls`), so cost/abuse is contained.
**Open / recommended.** Put the dashboard behind authentication or an IP allowlist
(or a reverse proxy with basic auth) before treating it as truly production. Until
then, treat holdings as semi-public.

## 8. Deployment & data drift
**Concern.** `data/` is gitignored, so `git pull` never updates parquets on AWS;
a schema change can break the dashboard if data isn't regenerated. Single EC2 host
(no HA); cron-dependent.
**Mitigation.** Documented deploy runbook (pull → regenerate parquet → restart);
deploys verify HTTP 200 + row counts; new tickers/columns are backfilled on deploy.
**Monitoring.** Post-deploy health check (`curl` 200, parquet row counts, module
imports). See `aws-deploy-gotchas` memory.

## 9. Model/API deprecation & cost
**Concern.** Model IDs retire (the roadmap's `claude-sonnet-4-20250514` was already
days from retirement); API cost scales with usage.
**Mitigation.** Pinned to current IDs; narrative uses Sonnet (cheap), moat uses
Opus quarterly. All API calls fail-soft. **No API-triggering controls on the public
dashboard** caps runaway cost.
**Monitoring.** Watch for deprecation notices; revisit model IDs each session.

## 10. Behavioral risk
**Concern.** A confident plain-English briefing can be **over-trusted**; thematic
framing can rationalize **over-concentration** (e.g. piling into AI).
**Mitigation.** The theme engine flags over-concentration (3+ in a theme) and gaps;
the narrative is told to question whether "more AI" is diversification or the same
bet; tone is honest about valuation/timing. Position sizing (Session 36) will make
sizing deliberate rather than ad hoc.
**Monitoring.** The Themes tab coverage/concentration summary; periodic review.

---

## How we monitor (operational)

- **Tests:** `pytest tests/` (20 tests) on every pipeline run; failures logged loud
  but non-fatal so alerts still send.
- **Deploy verification:** every AWS deploy checks HTTP 200 (local + external),
  parquet row counts, and module imports.
- **Fail-soft everywhere:** earnings, fundamentals, moat, narrative, themes all
  degrade to no-op on error; the core signal pipeline always completes.
- **Human-in-the-loop:** the system advises; it never trades.

## Review cadence

- **Each session:** skim this register; add any new risk introduced by new code.
- **Quarterly:** refresh moat scores, macro calendar; re-baseline valuation inputs.
- **After a week of live narratives:** quality review + prompt tuning.
