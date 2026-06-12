"""Interactive Q&A — ask the system about a ticker or the portfolio in plain English.

Reuses the SAME context builders the alerts use (theme_engine, auto_classify,
cash_deployment, valuation) so a Q&A answer can't drift from the daily briefing.
Signals ONLY — there is no news feed, and the prompt makes the model say so rather
than inventing a catalyst.

This spends a Claude API call, so it must stay BEHIND the dashboard password
(require_auth gates the whole app before the Ask tab is reachable). See memory
public-dashboard-no-api-controls.
"""

import os
import re

import pandas as pd

import auto_classify
import cash_deployment
import holdings_io
import theme_engine
import universe
import valuation

MODEL      = "claude-sonnet-4-6"   # same model as the daily narrative
MAX_TOKENS = 1200
MOAT_PATH  = "data/moat.parquet"

# Short uppercase words that collide with tickers but are almost never meant as one.
_STOPWORDS = {"A", "I", "IT", "IS", "ON", "IN", "OF", "TO", "DO", "AT", "OR", "BE",
              "AS", "SO", "ANY", "THE", "AND", "FOR", "ARE", "CAN", "YOU", "BUY",
              "ADD", "NOW", "WHY", "HOW", "WHAT", "WHEN", "TODAY", "HOLD", "SELL"}


def _universe():
    try:
        return set(universe.tickers())
    except Exception:
        return set()


def extract_tickers(question):
    """Universe tickers mentioned in the question, in order of appearance."""
    uni = _universe()
    seen, out = set(), []
    for t in re.findall(r"[A-Za-z]{1,5}", question):
        u = t.upper()
        if u in uni and u not in seen and u not in _STOPWORDS:
            seen.add(u)
            out.append(u)
    return out


def _moat_detail():
    if not os.path.exists(MOAT_PATH):
        return {}
    m = pd.read_parquet(MOAT_PATH)
    return {r["ticker"]: r for _, r in m.iterrows()}


def _ticker_block(tk, sig, holdings, tidx, cls_by, moat, deploy):
    raw = sig.get(tk)
    ns = theme_engine._name_status(tk, sig, holdings)
    if not ns or ns.get("no_data"):
        return f"{tk}: no signal data in the universe."

    lines = [f"{tk}:"]
    if holdings.get(tk):
        lines.append(f"  HELD at {holdings[tk]}")
    c = cls_by.get(tk)
    if c:
        lines.append(f"  Tier: {c['tier']} ({'; '.join(c['reasons'])})")
    ti = tidx.get(tk, {})
    if ti.get("themes"):
        lines.append(f"  Themes: {', '.join(ti['themes'])} ({ti.get('max_conv')} conviction)")
    lines.append(f"  Price ${ns.get('close')} | Widell {ns.get('wl_state')} | "
                 f"conviction {ns.get('conviction_score')}/10 | "
                 f"{ns.get('channel_zone')} channel | {ns.get('entry_status')}")
    lines.append(f"  Quality: F {ns.get('fundamental_score')}/5, moat {ns.get('moat_rating')}/5"
                 + (" (fits-profile)" if ns.get("fits_profile") else ""))
    if raw is not None:
        vt = valuation.valuation_tag(ns.get("close"), raw).lstrip(" |").strip()
        if vt:
            lines.append(f"  Valuation: {vt}")
    off, lo = ns.get("dist_52w_high"), ns.get("dist_52w_low")
    if off is not None and lo is not None:
        lines.append(f"  {abs(off):.0f}% below 52-wk high, {lo:.0f}% above 52-wk low")
    md = moat.get(tk)
    if md is not None and pd.notna(md.get("moat_summary")):
        lines.append(f"  Moat read: {md['moat_type']} — {md['moat_summary']} "
                     f"(key risk: {md['moat_risk']})")
    for a in deploy.get("actions", []):
        if a["ticker"] == tk:
            lines.append(f"  Deployment: {a['action']} +{a['suggested_pct']}% — {a['detail']}")
    for s in deploy.get("stops", []):
        if s["ticker"] == tk and s["status"] != "ok":
            lines.append(f"  Stop: ${s['stop']} ({s['dist_to_stop_pct']}% away) — {s['status']}")
    return "\n".join(lines)


def build_qa_context(question):
    """Return (context_text, detected_tickers) — the signal facts for the question."""
    holdings = holdings_io.load_positions()
    sig      = theme_engine._load_signals()
    tidx     = auto_classify._theme_index()
    cls      = auto_classify.classify_holdings()
    cls_by   = {c["ticker"]: c for c in cls["classifications"]}
    moat     = _moat_detail()
    try:
        deploy = cash_deployment.deployment()
    except Exception:
        deploy = {"actions": [], "stops": []}
    regime = theme_engine.tlt_regime(sig)

    lines = [f"QUESTION: {question}", "",
             "PORTFOLIO SNAPSHOT:",
             f"  {len(cls['core'])} core: {', '.join(cls['core'])}",
             f"  {len(cls['speculative'])} speculative: {', '.join(cls['speculative'])}",
             f"  Cash: {holdings_io.load_cash():.0f}% dry powder",
             f"  Bond regime: {regime['label']}", ""]

    tickers = extract_tickers(question)
    if tickers:
        lines.append("NAMES IN THE QUESTION:")
        for tk in tickers:
            lines.append(_ticker_block(tk, sig, holdings, tidx, cls_by, moat, deploy))
            lines.append("")
    elif deploy.get("actions"):
        lines.append("CASH DEPLOYMENT (priority actions today):")
        for a in deploy["actions"][:4]:
            lines.append(f"  {a['action']} {a['ticker']} +{a['suggested_pct']}% — {a['detail']}")
        lines.append("")

    return "\n".join(lines), tickers


SYSTEM_PROMPT = """You are Spencer's investing-intelligence assistant, answering a \
question about his portfolio or a specific name. He is a long-term, concentrated \
conviction investor (wide moats, secular trends toward the future, cash-flowing now; \
~10 best-in-class single names; signals are for entry timing and position validation, \
never trading).

Answer ONLY from the signal context provided (Widell state, conviction score, channel \
position / entry status, fundamentals, moat, valuation including our own forward-PE \
band, tier CORE vs SPECULATIVE, theme, the cash-deployment read, and the bond regime). \
CORE names are held through volatility — a core name showing weakness is a BUY signal, \
not a stop; only SPECULATIVE names carry a -7% stop.

You CANNOT see news, intraday prices, or anything outside this context. If asked about \
news or a catalyst, say plainly that you don't have a news feed, then answer from the \
signals you do have. Be honest and concise — a few short sentences or tight bullets, \
plain English. End with a clear bottom line: what, if anything, to do (often \
"nothing — wait"). This is not financial advice."""


def answer_question(question):
    """Return (answer_text, detected_tickers). Raises on missing key / API error."""
    import anthropic
    import narrative_alert
    narrative_alert.load_env()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise RuntimeError("ANTHROPIC_API_KEY not set")
    context, tickers = build_qa_context(question)
    client = anthropic.Anthropic()
    resp = client.messages.create(
        model=MODEL, max_tokens=MAX_TOKENS, thinking={"type": "disabled"},
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": context}])
    answer = "".join(b.text for b in resp.content if b.type == "text").strip()
    return answer, tickers


if __name__ == "__main__":
    import sys
    q = " ".join(sys.argv[1:]) or "What should I do with my cash today?"
    ctx, tks = build_qa_context(q)
    print("DETECTED TICKERS:", tks)
    print("=" * 70)
    print(ctx)
