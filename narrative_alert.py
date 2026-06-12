"""LLM narrative alert — the third daily Telegram message.

Runs AFTER the close pipeline (after telegram_alert.py in run_daily.sh). Where the
close alert dumps the raw signal tables, this one reads the same signals and asks
Claude to interpret them in plain English: is today a good environment to buy or
wait, which high-conviction names are actually actionable, and what's worth
watching tomorrow.

Context fed to Claude:
  - Date / day of week
  - SPY & QQQ market state (wl_state, composite, channel zone/position)
  - Universe counts (up / inconclusive / down, flip count)
  - Every conviction>=8 name (full signal row)
  - Flips today (ticker, direction, gap from flip, conviction)
  - High composite (>=2) names not yet in an up state
  - OPTIONAL enrichments, picked up automatically when their files exist:
      * holdings.yaml          -> personalize ("you hold ISRG at 5%")
      * data/earnings.parquet  -> 🗓️ earnings within 7 days (fetch_earnings.py)
      * data/moat.parquet      -> moat rating context (moat_score.py)

Claude returns five sections: MARKET CONTEXT, ACTIONABLE SETUPS, WATCH LIST,
PORTFOLIO CHECK, BOTTOM LINE. Sent via the same Telegram bot as the other alerts.

Design notes:
  - Model is claude-sonnet-4-6 (current Sonnet; the roadmap's claude-sonnet-4
    retires 2026-06-15). Sonnet is the cost-conscious tier for a daily job.
  - If anything fails (no API key, API error, bad data), we log and skip — the
    pipeline must never break because the narrative couldn't be generated.
  - The Telegram message is sent as PLAIN TEXT (no parse_mode). LLM prose can
    contain stray * _ [ ] that would make Telegram's Markdown parser reject the
    whole message.

Run via run_daily.sh (after telegram_alert.py) with SEND_TELEGRAM=1, or directly:
    python narrative_alert.py            # prints narrative, also sends to Telegram
    python narrative_alert.py --dry-run  # prints narrative + context, no send
"""

import os
import sys

import duckdb
import pandas as pd
import requests
from datetime import date, datetime

import valuation
import positions
import macro_calendar
import theme_engine
import position_sizing
import cash_deployment

MODEL          = "claude-sonnet-4-6"
MAX_TOKENS     = 1000
CONV_MIN       = 8     # high-conviction threshold
HIGH_COMP_MIN  = 2     # "high composite, not yet up" threshold
EARNINGS_SOON  = 7     # days; flag earnings within this window

VSA_PATH      = "data/stock_vsa.parquet"
FUND_PATH     = "data/fundamentals.parquet"
HOLDINGS_PATH = "holdings.yaml"
EARNINGS_PATH = "data/earnings.parquet"
MOAT_PATH     = "data/moat.parquet"
BRIEFING_PATH = "data/narrative_latest.json"   # last briefing, for the dashboard

DASHBOARD_URL = "http://18.188.180.99:8501"


# ---------------------------------------------------------------------------
# Env / Telegram (same pattern as telegram_alert.py / morning_alert.py)
# ---------------------------------------------------------------------------
def load_env():
    if not os.path.exists(".env"):
        return
    with open(".env") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            k, v = line.split("=", 1)
            os.environ[k] = v


def send_telegram(msg):
    token   = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("No Telegram credentials — skipping send.")
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    # Plain text on purpose — LLM prose breaks Telegram's Markdown parser.
    resp = requests.post(url, json={"chat_id": chat_id, "text": msg})
    if resp.status_code != 200:
        print(f"Telegram send failed ({resp.status_code}): {resp.text[:200]}")


# ---------------------------------------------------------------------------
# Signal loading
# ---------------------------------------------------------------------------
def load_signals():
    """Latest bar per ticker with the fields the narrative needs."""
    df = duckdb.query("""
        WITH latest AS (
            SELECT ticker, date, close, wl_state, wl_flip, regime,
                   composite, conviction_score, rsi_14,
                   flip_price, resistance, channel_pos, channel_zone,
                   wl_duration, vsa_label,
                   CASE
                       WHEN wl_state = 'up' THEN 'pullback'
                       WHEN wl_state = 'inconclusive' THEN 'breakout'
                       ELSE 'resistance'
                   END AS level_type,
                   ROUND((close - flip_price) / flip_price * 100, 1) AS gap_from_flip,
                   ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY date DESC) AS rn
            FROM 'data/stock_vsa.parquet'
        )
        SELECT * EXCLUDE (rn) FROM latest WHERE rn = 1
    """).df()

    val_cols = ["ttm_eps", "ttm_ocf", "shares", "ttm_eps_growth"]  # valuation inputs
    want = ["ticker", "fundamental_score", "rev_growth_yoy", "gross_margin"] + val_cols
    if os.path.exists(FUND_PATH):
        fund_all = pd.read_parquet(FUND_PATH)
        keep = [c for c in want if c in fund_all.columns]
        df = df.merge(fund_all[keep], on="ticker", how="left")
    # Ensure every expected column exists even if fundamentals/valuation are absent
    for c in want[1:]:
        if c not in df.columns:
            df[c] = pd.NA
    return df


def load_holdings():
    """holdings.yaml -> {ticker: 'weight string'} (incl CASH). Empty dict if absent."""
    import holdings_io
    return holdings_io.load_positions(include_cash=True)


def load_earnings():
    """data/earnings.parquet -> {ticker: days_until_earnings}. Empty if absent."""
    if not os.path.exists(EARNINGS_PATH):
        return {}
    try:
        e = pd.read_parquet(EARNINGS_PATH)
        if "next_earnings_date" not in e.columns:
            return {}
        e = e.dropna(subset=["next_earnings_date"]).copy()
        e["next_earnings_date"] = pd.to_datetime(e["next_earnings_date"]).dt.date
        today = date.today()
        return {
            r["ticker"]: (r["next_earnings_date"] - today).days
            for _, r in e.iterrows()
        }
    except Exception as ex:
        print(f"Could not read {EARNINGS_PATH}: {ex}")
        return {}


def load_moat():
    """data/moat.parquet -> {ticker: {rating, type, summary}}. Empty if absent."""
    if not os.path.exists(MOAT_PATH):
        return {}
    try:
        m = pd.read_parquet(MOAT_PATH)
        out = {}
        for _, r in m.iterrows():
            out[r["ticker"]] = {
                "rating":  r.get("moat_rating"),
                "type":    r.get("moat_type"),
                "summary": r.get("moat_summary"),
            }
        return out
    except Exception as ex:
        print(f"Could not read {MOAT_PATH}: {ex}")
        return {}


# ---------------------------------------------------------------------------
# Context formatting
# ---------------------------------------------------------------------------
def _earn_tag(ticker, earnings):
    d = earnings.get(ticker)
    if d is not None and 0 <= d <= EARNINGS_SOON:
        return f" | 🗓️ earnings in {d}d"
    return ""


def _hold_tag(ticker, holdings):
    w = holdings.get(ticker)
    return f" | HELD {w}" if w else ""


def _moat_tag(ticker, moat):
    m = moat.get(ticker)
    if not m or m.get("rating") in (None, "") or pd.isna(m.get("rating")):
        return ""
    return f" | moat {int(m['rating'])}/5 ({m.get('type','?')})"


def _fmt_row(r, holdings, earnings, moat):
    fund = (f"F{int(r['fundamental_score'])}/5"
            if pd.notna(r.get("fundamental_score")) else "F?/5")
    conv = int(r["conviction_score"]) if pd.notna(r["conviction_score"]) else 0
    gap  = f"{r['gap_from_flip']:+.1f}%" if pd.notna(r["gap_from_flip"]) else "n/a"
    lvl  = (f"{r['level_type']} ${r['resistance']:.2f}"
            if pd.notna(r["resistance"]) else r["level_type"])
    days = int(r["wl_duration"]) if pd.notna(r["wl_duration"]) else 0
    return (
        f"  {r['ticker']}: ${r['close']:.2f} | {r['wl_state']} {days}d "
        f"| conv {conv}/10 | {fund} | zone {r['channel_zone']} "
        f"(pos {r['channel_pos']:.2f}) | {lvl} | gap-from-flip {gap}"
        f"{_hold_tag(r['ticker'], holdings)}"
        f"{_earn_tag(r['ticker'], earnings)}"
        f"{_moat_tag(r['ticker'], moat)}"
        f"{valuation.valuation_tag(r['close'], r)}"
    )


def build_context(df, holdings, earnings, moat):
    today = date.today()
    lines = [f"DATE: {today.strftime('%A, %B %d, %Y')}", ""]

    # --- Market backdrop ---
    lines.append("MARKET (the read on environment):")
    for sym in ("SPY", "QQQ"):
        row = df[df["ticker"] == sym]
        if not len(row):
            continue
        r = row.iloc[0]
        pos = f"{r['channel_pos']:.2f}" if pd.notna(r["channel_pos"]) else "n/a"
        rsi = f" | RSI {r['rsi_14']:.0f}" if pd.notna(r["rsi_14"]) else ""
        lines.append(
            f"  {sym}: {r['wl_state']} | composite {int(r['composite'])} "
            f"| zone {r['channel_zone']} (pos {pos}){rsi}"
        )
    lines.append("")

    # --- Upcoming macro the price data can't see (CPI / FOMC) ---
    macro = macro_calendar.nearby_events(ahead_days=10, back_days=2)
    if macro:
        lines.append("UPCOMING MACRO (events the signals can't see):")
        for e in macro:
            lines.append(f"  {e['event']} — {macro_calendar.when_str(e['days'])} "
                         f"({e['date']})")
        lines.append("")

    # --- Theme intelligence (secular-trend lens: bond regime, coverage, gaps,
    #     concentration). Defensive — never let a theme error break the briefing. ---
    try:
        cov = theme_engine.get_portfolio_theme_coverage()
        lines.append("THEME INTELLIGENCE (secular-trend lens):")
        lines.append(f"  Bond regime: {cov['tlt_regime']['label']}")
        lines.append(f"  Coverage: {cov['themes_covered']} of {cov['total_themes']} "
                     f"themes held | {cov['held_count']} positions "
                     f"(target {cov['target_min']}-{cov['target_max']})")
        if cov["gaps"]:
            lines.append("  Gaps (no exposure) — best entry now:")
            for g in cov["gaps"]:
                be = g["best_entry_now"]
                if be and not be.get("no_data"):
                    star = " ⭐(fits profile)" if be.get("fits_profile") else ""
                    lines.append(f"    - {g['name']} ({g['conviction']}): {be['ticker']} "
                                 f"{be['entry_status']}, conv {be.get('conviction_score')}/10, "
                                 f"{be.get('channel_zone')}{star}")
                else:
                    lines.append(f"    - {g['name']} ({g['conviction']})")
        if cov["concentrated"]:
            lines.append("  Concentrated (3+ in one theme): " + "; ".join(
                f"{c['name']} ({', '.join(c['held_names'])})" for c in cov["concentrated"]))
        if cov["unthemed_holdings"]:
            lines.append("  Off-thesis holdings (in no theme): " + ", ".join(
                u["ticker"] + (f" — {u['note']}" if u["note"] else "")
                for u in cov["unthemed_holdings"]))
        lines.append("")
    except Exception as e:
        print(f"theme intelligence unavailable: {e}")

    # --- Position sizing (advisory, conviction-led) — biggest over/underweights ---
    try:
        siz = position_sizing.compute_sizing()
        adds  = sorted([r for r in siz["rebalance"] if r["action"] == "ADD"],
                       key=lambda r: r["delta"], reverse=True)[:3]
        trims = sorted([r for r in siz["rebalance"] if r["action"] == "TRIM"],
                       key=lambda r: r["delta"])[:3]
        if adds or trims or siz["starters"]:
            lines.append("POSITION SIZING (advisory — conviction-led targets vs your weights):")
            if adds:
                lines.append("  Underweight vs conviction (add): "
                             + ", ".join(f"{r['ticker']} {r['delta']:+.1f}%" for r in adds))
            if trims:
                lines.append("  Overweight / low-conviction (trim): "
                             + ", ".join(f"{r['ticker']} {r['delta']:+.1f}%" for r in trims))
            if siz["starters"]:
                s = siz["starters"][0]
                lines.append(f"  Top gap starter: {s['ticker']} ~{s['starter']:.1f}% "
                             f"({s['theme']}, conv {s['conviction']}, {s['entry_status']})")
            lines.append("")
    except Exception as e:
        print(f"position sizing unavailable: {e}")

    # --- Universe counts ---
    up   = int((df["wl_state"] == "up").sum())
    inc  = int((df["wl_state"] == "inconclusive").sum())
    down = int((df["wl_state"] == "down").sum())
    flips = int(df["wl_flip"].sum())
    lines.append(
        f"UNIVERSE ({len(df)} names): {up} up, {inc} inconclusive, "
        f"{down} down | {flips} flip(s) today"
    )
    lines.append("")

    # --- High conviction ---
    hc = df[(pd.notna(df["conviction_score"])) &
            (df["conviction_score"] >= CONV_MIN)].sort_values(
        "conviction_score", ascending=False)
    lines.append(f"HIGH CONVICTION (score >= {CONV_MIN}) — {len(hc)} name(s):")
    if len(hc):
        for _, r in hc.iterrows():
            lines.append(_fmt_row(r, holdings, earnings, moat))
    else:
        lines.append("  none today")
    lines.append("")

    # --- Flips today ---
    fl = df[df["wl_flip"] == True].sort_values("composite", ascending=False)
    lines.append(f"FLIPS TODAY — {len(fl)} name(s):")
    if len(fl):
        for _, r in fl.iterrows():
            lines.append(_fmt_row(r, holdings, earnings, moat))
    else:
        lines.append("  none today")
    lines.append("")

    # --- High composite, not yet up ---
    hicomp = df[(df["composite"] >= HIGH_COMP_MIN) &
                (df["wl_state"] != "up")].sort_values("composite", ascending=False)
    lines.append(f"HIGH SCORE (composite >= {HIGH_COMP_MIN}, not yet up) "
                 f"— {len(hicomp)} name(s):")
    if len(hicomp):
        for _, r in hicomp.iterrows():
            lines.append(_fmt_row(r, holdings, earnings, moat))
    else:
        lines.append("  none today")
    lines.append("")

    # --- Held positions — trim/exit review (covers every name you own, not just
    #     ones flagged elsewhere today). CASH is dry powder, surfaced separately
    #     so Claude can size "buy vs wait" against available cash. ---
    cash = holdings.get("CASH")
    stock_holdings = {k: v for k, v in holdings.items() if k != "CASH"}
    if stock_holdings:
        lines.append("YOUR POSITIONS (held) — trim/exit review:")
        for t in sorted(stock_holdings):
            sub = df[df["ticker"] == t]
            if not len(sub):
                lines.append(f"  {t} ({stock_holdings[t]}): no signal data")
                continue
            r = sub.iloc[0]
            status, reason = positions.assess_position(r["channel_zone"], r["wl_state"])
            note = f" — {reason}" if reason else ""
            lines.append(
                f"  {t} ({stock_holdings[t]}): ${r['close']:.2f} | {r['wl_state']} "
                f"| zone {r['channel_zone']} | {status}{note}"
                f"{valuation.valuation_tag(r['close'], r)}"
            )
        lines.append("")
    if cash:
        lines.append(f"DRY POWDER: {cash} cash available to deploy")
        lines.append("")

    # --- Cash deployment (priority-ordered "where the next dollar goes" + the
    #     speculative stops and any thesis erosion). Defensive — never break the
    #     briefing if the engine hiccups. ---
    try:
        d = cash_deployment.deployment()
        lines.append("CASH DEPLOYMENT (where the next dollar goes — advisory):")
        lines.append(f"  Classification: {d['n_core']} core, {d['n_speculative']} "
                     f"speculative | {d['cash_pct']:.0f}% cash"
                     + (f" (${d['cash_dollars']:,})" if d['cash_dollars'] else "")
                     + " dry powder")
        if d["actions"]:
            lines.append("  Priority actions (deploy top-down, stage in tranches):")
            for a in d["actions"][:4]:
                dol = f" ~${a['suggested_dollars']:,}" if a.get("suggested_dollars") else ""
                lines.append(f"    - {a['action']} {a['ticker']} +{a['suggested_pct']}%"
                             f"{dol} [{a['tier']}]: {a['detail']}")
        elif d["hold_cash"]:
            lines.append(f"  {d['hold_cash']['message']}")
            for t in d["hold_cash"]["triggers"][:3]:
                lines.append(f"    - would trigger: {t['detail']}")
        watch = [s for s in d["stops"] if s["status"] in ("watch", "triggered")]
        if watch:
            lines.append("  Speculative stops approaching (−7% from entry):")
            for s in watch:
                tag = "STOP HIT" if s["status"] == "triggered" else "watch"
                lines.append(f"    - {s['ticker']} ${s['current']} vs stop ${s['stop']} "
                             f"({s['dist_to_stop_pct']}% away) — {tag}")
        if d["thesis_alerts"]:
            lines.append("  Thesis integrity (core — evidence eroded):")
            for a in d["thesis_alerts"]:
                lines.append(f"    - {a['ticker']}: {a['detail']}")
        lines.append("")
    except Exception as e:
        print(f"cash deployment unavailable: {e}")

    return "\n".join(lines)


SYSTEM_PROMPT = """You are an investing advisor writing a short daily briefing for \
Spencer, a long-term investor (NOT a trader). His approach:
- Owns high-quality companies with durable moats and holds them for years.
- Buys on pullbacks; refuses to buy at the top of a regression channel (zone \
"extended" or "upper" = expensive, "lower"/"middle" = better entry).
- Uses Widell Line flips as TIMING CONFIRMATION, not a primary buy signal. A flip \
in a weak tape is usually noise.
- Conviction score >= 8 = his highest-priority setups.
- Cares about durable moats. When a name shows a moat rating, factor it in: a \
pullback in a wide-moat name (4-5/5) is more buyable and more forgiving than the \
same setup in a no-moat (1-2/5) name, which needs tighter timing.
- Keeps cash as dry powder (shown as DRY POWDER). Having cash to deploy makes a \
genuinely good pullback more actionable, but he will NOT force a trade just because \
cash is sitting idle — a weak tape is still a reason to wait.
- Some names show valuation (PE / PEG / P/OCF, where P/OCF is a free-cash-flow \
proxy). Treat it as CONTEXT, not a gate: a wide-moat compounder often deserves a \
premium multiple, so don't reject quality just for a high PE — but do flag when a \
setup means paying a stretched price (e.g. high PEG), especially for thinner moats.
- Invests CONCENTRATED and THEMATIC: ~10 best-in-class single names across secular \
trends (AI infra/software, power & grid, reindustrialization, defense, critical \
materials, etc.) — no index/ETF positions. His ideal name is a WIDE MOAT business \
in a future-facing secular trend that is CASH-FLOWING NOW at a sane price (marked \
⭐ "fits profile"). The bond market (TLT) is his key macro regime gauge.
- Wants simplicity. He does not want to decode tables — he wants to be told what, \
if anything, to actually do.

You are given today's signals. The system can't see macro news (geopolitics, \
surprises) — if the breadth looks off (many flips but market down, SPY/QQQ extended \
and weak), say so and treat today's flips with appropriate skepticism.

Scheduled macro IS provided in UPCOMING MACRO (CPI prints, FOMC decisions). If one \
is within ~2 days or happened today/yesterday, weight it heavily: price action and \
fresh Widell flips around CPI/Fed are usually noise, and it's typically better to \
wait until after the event before acting. Call this out in MARKET CONTEXT.

Use THEME INTELLIGENCE actively, woven into the sections (do NOT add a new section):
- MARKET CONTEXT: factor in the bond regime (TLT tailwind favors growth/AI; headwind \
pressures valuations).
- ACTIONABLE SETUPS: when there's dry powder, surface the best entry in an UNCOVERED \
high-conviction theme (a "gap") even if its conviction is below 8 — a ⭐ name at AT \
ENTRY in a high-conviction gap is exactly the wide-moat / secular / cash-flowing \
profile he wants. Name the gap and the entry.
- PORTFOLIO CHECK: also flag over-concentration (3+ in one theme) and off-thesis \
holdings (names in no theme) when relevant. Use POSITION SIZING here too — call out \
where he is most underweight vs conviction (a name worth adding to) or overweight in \
a low-conviction name (worth trimming). Sizing is advisory, not a mechanical rebalance.

There is also a CASH DEPLOYMENT block — the derived, priority-ordered answer to \
"where does my next dollar go," plus speculative stop distances and any thesis \
erosion. Use it to write the PORTFOLIO ACTION section below. Core names are held \
through volatility (a core name showing weakness is a BUY signal, never a stop); \
only speculative names carry a −7% stop.

Write EXACTLY these six sections, plain English, no jargon, no tables, concise:

MARKET CONTEXT
2-3 sentences on what SPY/QQQ are telling us. Is this a good environment to be \
buying, or to wait?

ACTIONABLE SETUPS
One short bullet per conviction>=8 name (or write "None today."). For each: is it \
in a buyable entry zone right now, or is it extended/chasing? Worth acting on or \
wait? If Spencer already holds it, say so and frame as add-vs-hold. Flag 🗓️ \
earnings within 7 days as a reason to wait.

WATCH LIST
One short bullet per name approaching a signal but not ready — what to watch for \
tomorrow. "None today." is fine.

PORTFOLIO CHECK
Look at YOUR POSITIONS. Call out only the names flagged TRIM (rich, above the \
channel top - consider trimming into strength) or REVIEW (breaking down - reassess \
the thesis); one short bullet each with what you'd do. If every holding is HOLD, \
write "All holdings healthy - nothing to trim or review." Don't list healthy names.

PORTFOLIO ACTION
Translate the CASH DEPLOYMENT block into plain English. If there are priority \
actions, give the top 1-3 as short bullets: what to buy/add, how much, and why \
(core weakness add, theme-gap starter, or beaten-down speculative). If there are \
none, say "No compelling entries - hold cash, patience is the edge" and name the \
one trigger worth waiting for. Then, if any speculative position is approaching its \
-7% stop, add a one-line watch. Finally, surface any thesis-integrity alert (a core \
name whose fundamentals eroded) as a "review the thesis" line.

BOTTOM LINE
One sentence: what should Spencer actually do today (often "nothing — wait").

Keep the whole thing tight enough to read on a phone. This is sent as a plain-text \
message, so DO NOT use any Markdown formatting — no #, no **bold**, no horizontal \
rules (---). Put each of the four section headers in CAPS on its own line, and use \
a simple "- " for bullets."""


def call_claude(context):
    import anthropic
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise RuntimeError("ANTHROPIC_API_KEY not set")
    client = anthropic.Anthropic()
    resp = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        thinking={"type": "disabled"},  # 1000-token budget; keep it all for prose
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": context}],
    )
    return "".join(b.text for b in resp.content if b.type == "text").strip()


# ---------------------------------------------------------------------------
# Reusable entry points — shared by this CLI and the dashboard so the briefing
# logic lives in exactly one place.
# ---------------------------------------------------------------------------
def generate_narrative():
    """Load the latest signals, build context, and return (narrative, context).

    Raises on failure (missing data, no API key, API error) — the caller decides
    how to handle it. Calls load_env() so it works both from the CLI and when
    imported by the dashboard.
    """
    load_env()
    df       = load_signals()
    holdings = load_holdings()
    earnings = load_earnings()
    moat     = load_moat()
    context  = build_context(df, holdings, earnings, moat)
    narrative = call_claude(context)
    return narrative, context


def save_briefing(narrative):
    """Persist the briefing + timestamps so the dashboard can show it without
    spending an API call on every page view."""
    import json
    payload = {
        "date":         date.today().strftime("%Y-%m-%d"),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "narrative":    narrative,
    }
    os.makedirs(os.path.dirname(BRIEFING_PATH), exist_ok=True)
    with open(BRIEFING_PATH, "w") as f:
        json.dump(payload, f, indent=2)


def load_briefing():
    """Return the last saved briefing dict ({date, generated_at, narrative}),
    or None if none has been generated yet / the file is unreadable."""
    import json
    if not os.path.exists(BRIEFING_PATH):
        return None
    try:
        with open(BRIEFING_PATH) as f:
            return json.load(f)
    except Exception:
        return None


def main():
    dry_run = "--dry-run" in sys.argv
    load_env()

    try:
        narrative, context = generate_narrative()
    except Exception as e:
        print(f"Narrative generation failed — skipping narrative alert: {e}")
        return

    if dry_run:
        print("=== CONTEXT ===")
        print(context)
        print("=== /CONTEXT ===\n")

    today = date.today().strftime("%Y-%m-%d")
    msg = f"🧭 Daily Briefing — {today}\n\n{narrative}\n\n{DASHBOARD_URL}"

    print(msg)
    if not dry_run:
        save_briefing(narrative)   # persist for the dashboard before pushing
        try:
            # Maintain the position tracker (entry-price anchors for speculative
            # stops + fundamental baselines for thesis integrity). After the
            # briefing has already read the OLD baseline, so a fundamental drop is
            # caught on the transition, then the baseline moves forward.
            cash_deployment.record_positions()
        except Exception as e:
            print(f"position tracker update skipped: {e}")
        send_telegram(msg)
        print("\nNarrative alert sent.")


if __name__ == "__main__":
    main()
