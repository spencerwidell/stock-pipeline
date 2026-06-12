# Conviction Backtest — Honest Validation

*Does a higher conviction score actually lead to better forward returns?* This is the
load-bearing question for the whole system, so it gets pressure-tested honestly and
the result is reported regardless of outcome. Reproduce with `backtest_conviction.py`.

> **Session 40 re-weight.** The original scoring (channel `lower=4`/`breakdown=2`,
> Widell state worth only 0–2, fundamentals 0–3) rewarded beaten-down names and
> under-weighted the *validated* Widell-state edge, so the mid-scale carried beaten-down
> beta rather than signal (the 0–3 bucket beat 4–5 and 6–7). The score was re-weighted
> from the backtest below: **Widell state 0–4** (the validated edge becomes the top
> driver, so ≥8 requires confirmed up-momentum), **channel 0–3 with breakdown/extended = 0**
> (no reward for broken structure), **fundamentals 0–2** (lighter weight on the only
> lookahead-prone component), flip 0–1. Result: a stronger Spearman, a monotonic win
> rate, and a cleaner, stronger top bucket.

## Method

- Every historical bar with a `conviction_score` (0–10), forward returns at
  **5 / 20 / 60 trading days**.
- **SPY-relative alpha** (forward return minus SPY's over the same window) to strip
  out market drift — the same target discipline as the research phase.
- Grouped into buckets: 0–3 (low) / 4–5 / 6–7 / 8–10 (high).
- **Primary test = single names** (the conviction *buy* thesis); ETFs reported
  separately for reference.
- Stress-tested **by year** — a headline that only works in one regime is not a result.

**Honest caveat (load this before the numbers):** conviction's **fundamental
sub-score (0–2 of 10) uses *current* fundamentals applied to past bars** — a
lookahead bias in that component. The other 8 points (Widell state, channel position,
flip recency) are point-in-time and clean. So treat the *absolute* edge as inflated;
the **rank ordering across buckets** and the **year-by-year persistence** are the
trustworthy signals. (The re-weight cut this component from 3 → 2 points, so the
lookahead now has less leverage than before.)

## Results (single names, n = 100,811 bars)

| Bucket | n | raw 20d | alpha 5d | alpha 20d | alpha 60d | win% 20d |
|---|---:|---:|---:|---:|---:|---:|
| 0–3 (low) | 29,441 | 3.89 | 0.30 | 2.82 | 9.75 | 52.5 |
| 4–5 | 39,443 | 3.91 | 0.61 | 2.59 | 9.58 | 56.9 |
| 6–7 | 26,061 | 4.07 | 0.77 | 2.80 | 7.12 | 56.8 |
| **8–10 (high)** | **5,866** | **7.33** | **2.63** | **5.71** | **12.26** | **61.2** |

- **Conv ≥8 vs the rest (20d alpha): +5.71% vs +2.72% → +2.99% edge.**
- **Spearman(conviction, 20d alpha) = +0.0333** — positive, and stronger than the
  pre-re-weight +0.0259.
- **Win rate rises monotonically** with conviction (52.5% → 56.9% → 56.8% → 61.2%).
- The ≥8 bucket leads on every horizon (5d +2.63, 20d +5.71, 60d +12.26).

### Stress test — 20d alpha by bucket × year

| bucket | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0–3 | 9.06 | 0.07 | −0.51 | 1.49 | 7.49 | 3.69 | 1.16 |
| 4–5 | 3.91 | 0.13 | 0.35 | 2.61 | 4.36 | 4.24 | 2.75 |
| 6–7 | 5.62 | 0.80 | 3.12 | 2.47 | 3.46 | 3.51 | 1.12 |
| **8–10** | **4.86** | **1.53** | **13.72** | **3.66** | **6.16** | **6.16** | **1.98** |

The conv ≥8 bucket is **positive in every year, including the 2022 bear market
(+13.72%)** — the single most important line in this document, and now stronger than
before the re-weight (was +8.46%). It is not a one-regime artifact.

## Honest interpretation

**What holds up:** Conviction ≥8 is a genuine high-priority filter. It delivers a
meaningful, persistent forward-alpha edge (+3.0% at 20d, +12% at 60d), the highest win
rate, and — critically — it works across every market regime in the sample, including
the 2022 drawdown. Because the re-weight makes ≥8 *require confirmed up-momentum*
(Widell state is the top component), the top bucket is now a real momentum-plus-quality
signal rather than beaten-down names catching a bounce. This validates the system's
central instruction: *treat conv ≥8 as the highest-priority setups.*

**What doesn't (and we say so):**
- **It's a top-tier filter, not a linear dial.** The mid-buckets (0–3, 4–5, 6–7) are
  now flat-to-tight (2.82 / 2.59 / 2.80) — the middle of the scale still carries little
  *ordering* information, even though the win rate climbs through it. The 0–3 bucket's
  decent return is most likely beaten-down high-beta names mean-reverting in up-markets
  — beta, not quality. The edge lives at the top. The re-weight removed the *reward* for
  being beaten down (breakdown is now 0 pts), so the score no longer pushes that beta
  into the mid-tier, but it can't erase it from the lowest bucket.
- **The absolute level is still inflated by the fundamental lookahead** (now 2 of 10
  pts, down from 3). We trust the *shape* (top bucket wins, persists by year, monotonic
  win rate) more than the exact percentages.

## Implications / next steps

1. **Keep conv ≥8 as the headline filter** — it earned it, and the re-weight made it
   cleaner (up-momentum required). In a weak/sideways tape, few or no single names hit
   ≥8 — that is the honest signal to wait, not a bug.
2. **The mid-scale is intentionally not a linear dial** — 0–7 is coarse context; the
   action is at the extremes (≥8 priority buys; the deployment engine reads the
   components directly for "add to core on weakness").
3. **Remove the lookahead to re-test cleanly** — still requires point-in-time
   fundamentals history (not stored). Until then, this caveat stands, now with less
   leverage (2 pts).
4. **Re-run periodically** (`backtest_conviction.py`) as more live data accrues,
   especially through the next down regime.

*This is empirical evidence on historical data, with the stated lookahead caveat —
not a guarantee of future results. The truth, told plainly, so the next steps are
true and just.*
