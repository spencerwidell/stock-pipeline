# Key Objectives — Canonical Mission

> *Empirical rigor earned the foundations. The system now exists to turn those
> foundations into clear, honest, plain-English decisions for a specific investing
> philosophy: wide moats, secular trends toward the future, cash-flowing now, held
> in a concentrated portfolio of 10 best-in-class names.*

This is the north star. Every feature is judged against it; if a change doesn't
ladder up to this statement, it doesn't ship.

## Research was the means; the product is the end

The empirical research phase (Sessions 1–21) is **complete**. It validated the
Widell Line, the signal stack, and the discipline of stress-testing every claim —
and it found the honest ceiling of what raw signals can predict. That work was not
the goal; it was how the foundations were *earned*. The goal is the **product**: a
decision-support system that interprets the validated stack into plain-English
calls for one investor. (Origin story in `docs/PRODUCT_ROADMAP.md`, Part 1.)

## The investing philosophy is a design constraint

The system is built around one investor and one philosophy. These are constraints,
not preferences — they shape every default:

- **Concentrated** — ~10 positions (max 10–15). Enough to move the needle, few
  enough to know deeply.
- **Conviction-driven** — act on the highest-quality setups (conviction ≥ 8), not
  on every flicker.
- **Wide moat** — own durable competitive advantages (moat 4–5), not commodities.
- **Secular trends toward the future** — every name should fit a multi-year trend.
- **Cash-flowing now** — a real business at a sane price, not just a story.
- **Long-term horizon** — signals are for *entry timing and position validation*,
  never for trading in and out.
- **Best-in-class single names** — the single best company in a trend, **no index
  exposure**.
- **Macro-aware** — the bond market (TLT) and the CPI/FOMC calendar set whether it's
  an environment to act or wait.

The ideal name is the intersection: **wide moat × future-facing secular trend ×
cash-flowing now** (surfaced as the ⭐ "fits profile" flag).

## What the system DOES

- **Interprets signals into plain-English decisions** — "what, if anything, should
  I do today?" — so a busy investor doesn't have to decode tables.
- **Flags gaps in theme coverage** — which secular trends you don't own yet.
- **Surfaces the best entry** in each theme (conviction + channel position).
- **Warns on macro headwinds and earnings risk** — bond regime, CPI/FOMC proximity,
  earnings within 7 days.
- **Manages what's owned** — flags names to trim (extended) or review (breaking down).
- **Stays honest** — names valuation and timing risk out loud; treats flips in weak
  tape or around macro events as likely noise.

## What the system does NOT do

- **Does not trade automatically** — it never places an order; human-in-the-loop is
  the ultimate control.
- **Does not give financial advice** — it is a personal decision-support tool.
- **Does not replace fundamental research** — it frames and prioritizes; the investor
  still does the deep work on a business.
- **Does not guarantee outcomes** — signals are empirical observations on historical
  data; past performance does not predict future results.
- **Does not chase a black-box edge** — ML was explored and capped; the value is the
  interpreted, explainable stack, not an opaque predictor.
- **Does not hold index/ETF positions** — ETFs in the universe are signal proxies and
  regime gauges, not buys.

## What "good" looks like

- The investor reads one briefing and knows what to do (often "wait").
- Entries happen in lower/middle channel on confirmation, not chasing.
- The portfolio stays ~10–15 best-in-class names, deliberately spread across
  high-conviction secular themes, with gaps and over-concentration made visible.
- The system runs unattended and degrades gracefully when a source fails.
