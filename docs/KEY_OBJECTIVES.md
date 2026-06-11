# Key Objectives

The north star for the stock-pipeline system. Every feature is judged against
these objectives; if a change doesn't serve one of them, it doesn't ship.

## Who this is for

One user — Spencer — a **concentrated, high-conviction, long-term investor**:

- Holds ~10 (max 10–15) **best-in-class single names** — no index/ETF positions.
- Wants the single best company in each **secular trend**, not the basket.
- Uses signals for **entry timing and position validation**, not trading.
- Ideal company: **wide moat × future-facing secular trend × cash-flowing now.**
- Intellectually honest about valuation and timing risk; will wait.

## Primary objective

**Turn raw market signals into clear, plain-English decisions a busy long-term
investor can act on** — "what, if anything, should I do today?" — without sitting
in front of charts. The system interprets; the human decides.

## Supporting objectives

1. **Don't buy at the top.** Surface regression-channel position so entries happen
   on pullbacks (lower/middle), not at extended highs.
2. **Time entries with confirmation, not prediction.** Widell Line flips are timing
   confirmation; conviction score (0–10) ranks setup quality; ≥8 = highest priority.
3. **Own quality.** Fundamental score (0–5), moat rating (1–5), and valuation
   (PE/PEG/P-OCF, as context not a gate) keep the focus on durable businesses.
4. **Think in secular themes.** Map every name to a multi-year trend; expose theme
   coverage, gaps, concentration, and best-in-class entries so the portfolio is a
   deliberate set of bets, not an accumulation.
5. **Respect macro.** The bond market (TLT) regime and the CPI/FOMC calendar frame
   whether it's an environment to act or wait — the system can't see news, so it
   says so.
6. **Manage what's owned.** Trim/exit framework flags held names that are extended
   (trim) or breaking down (review). No hard stops — long-term framing.
7. **Stay simple and trustworthy.** Three daily Telegram alerts + one dashboard.
   Fail-soft everywhere: a data or API hiccup never breaks the pipeline.

## Explicit non-goals

- **Not a trading system.** No intraday signals, no hard stops, no churn.
- **Not a robo-advisor / auto-trader.** It never places orders. Human-in-the-loop.
- **Not index exposure.** ETFs in the universe are signal proxies, not buys.
- **Not a backtest-chasing ML product.** ML was explored (Session 18–20) and
  capped; the edge is the interpreted signal stack, not a black-box predictor.

## What "good" looks like

- Spencer reads one briefing and knows what to do (usually "wait").
- Entries happen in lower/middle channel on confirmation, not chasing.
- The portfolio stays ~10–15 names, deliberately spread across high-conviction
  themes, with gaps and over-concentration made visible.
- The system runs unattended and degrades gracefully when a source fails.
