"""Lightweight pre-market / morning check — no pipeline re-run.

Loads yesterday's Widell Line state (latest bar per ticker from
data/stock_vsa.parquet), pulls live prices from the Polygon snapshot endpoint,
and pushes three actionable sections to Telegram:

  1. HIGH CONVICTION IN ENTRY RANGE — conviction >= 8 names trading within 3%
     of their pullback target. Buyable right now.
  2. BREAKOUT WATCH — inconclusive names within 5% of their breakout level that
     gapped/moved >1% at the open. May be breaking out today.
  3. NOTABLE MOVES — anything up or down >3% at the open. Context only.

If nothing qualifies, it still sends a heartbeat so you know it ran.

Note on levels: the pipeline stores one swing-high `resistance` column whose
meaning is state-dependent — it's the pullback target for an up-state name and
the breakout level for an inconclusive one (same convention as
telegram_alert.py / the dashboard's level_type).

Run on a weekday morning after the daily pipeline has produced an up-to-date
parquet. Always sends — no SEND_TELEGRAM flag.
"""

import os
import requests
import pandas as pd
import duckdb
from datetime import date

import positions
import theme_engine

CONV_MIN          = 8     # high-conviction threshold
ENTRY_RANGE_PCT   = 3.0   # within X% of pullback target = entry range
BREAKOUT_NEAR_PCT = 5.0   # within X% of breakout level = on breakout watch
BREAKOUT_MOVE_PCT = 1.0   # min open move to flag a possible breakout
NOTABLE_MOVE_PCT  = 3.0   # |open move| above this = notable
EARNINGS_SOON     = 7     # flag earnings within this many days
EARNINGS_PATH     = "data/earnings.parquet"
HOLDINGS_PATH     = "holdings.yaml"


def load_env():
    with open(".env") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            k, v = line.split("=", 1)
            os.environ[k] = v


load_env()
TOKEN   = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
API_KEY = os.environ["POLYGON_API_KEY"]


def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})


# ---------------------------------------------------------------------------
# 1. Yesterday's state — latest bar per ticker
# ---------------------------------------------------------------------------
def load_latest():
    return duckdb.query("""
        WITH latest AS (
            SELECT ticker, date, close, wl_state, conviction_score, resistance,
                   channel_zone,
                   ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY date DESC) as rn
            FROM 'data/stock_vsa.parquet'
        )
        SELECT ticker, date, close AS prev_close, wl_state,
               conviction_score, resistance, channel_zone
        FROM latest WHERE rn = 1
    """).df()


# ---------------------------------------------------------------------------
# 2. Live prices via Polygon snapshot (single bulk call)
# ---------------------------------------------------------------------------
def fetch_snapshot(tickers):
    """Return {ticker: (current_price, overnight_move_pct)} from the snapshot."""
    url = "https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/tickers"
    resp = requests.get(url, params={"tickers": ",".join(tickers), "apiKey": API_KEY})
    data = resp.json()
    out = {}
    for t in data.get("tickers", []):
        sym = t.get("ticker")
        # prefer last trade, then latest minute close, then today's day close
        price = (t.get("lastTrade", {}).get("p")
                 or t.get("min", {}).get("c")
                 or t.get("day", {}).get("c"))
        move = t.get("todaysChangePerc")
        if not price:
            continue
        out[sym] = (price, move)
    return out


def pct(a, b):
    """% distance of a from b."""
    if pd.isna(a) or pd.isna(b) or b == 0:
        return None
    return (a - b) / b * 100.0


def load_earnings():
    """data/earnings.parquet -> {ticker: days_until_earnings}. Empty if absent."""
    if not os.path.exists(EARNINGS_PATH):
        return {}
    try:
        e = pd.read_parquet(EARNINGS_PATH).dropna(subset=["next_earnings_date"])
        e["next_earnings_date"] = pd.to_datetime(e["next_earnings_date"]).dt.date
        today = date.today()
        return {r["ticker"]: (r["next_earnings_date"] - today).days
                for _, r in e.iterrows()}
    except Exception:
        return {}


def earn_tag(ticker, earnings):
    """' 🗓️Nd' if `ticker` reports within EARNINGS_SOON days, else ''."""
    d = earnings.get(ticker)
    return f" 🗓️{d}d" if d is not None and 0 <= d <= EARNINGS_SOON else ""


def load_holdings():
    """holdings.yaml -> {ticker: 'weight'}. Empty dict if absent/unreadable."""
    if not os.path.exists(HOLDINGS_PATH):
        return {}
    try:
        import yaml
        with open(HOLDINGS_PATH) as f:
            raw = yaml.safe_load(f) or {}
        return {str(k).upper(): str(v).strip() for k, v in raw.items() if v is not None}
    except Exception:
        return {}


def hold_tag(ticker, holdings):
    """' 💼HELD w' if `ticker` is a current holding, else ''."""
    w = holdings.get(ticker)
    return f" 💼HELD {w}" if w else ""


def main():
    df = load_latest()
    today = date.today().strftime("%Y-%m-%d")
    snap = fetch_snapshot(df["ticker"].tolist())
    earnings = load_earnings()
    holdings = load_holdings()

    high_conv, breakout, notable, position_flags = [], [], [], []

    for _, r in df.iterrows():
        tkr = r["ticker"]
        if tkr not in snap:
            continue
        price, move = snap[tkr]
        state = r["wl_state"]
        conv  = r["conviction_score"]
        level = r["resistance"]   # pullback target (up) / breakout level (inconclusive)

        from_pullback = pct(price, level)   # relevant when state == 'up'
        from_breakout = pct(price, level)   # relevant when state == 'inconclusive'

        # Section 1 — high conviction in entry range
        if (pd.notna(conv) and conv >= CONV_MIN
                and from_pullback is not None and abs(from_pullback) <= ENTRY_RANGE_PCT):
            high_conv.append((tkr, price, int(conv), from_pullback, state))

        # Section 2 — breakout watch
        if (state == "inconclusive"
                and from_breakout is not None and abs(from_breakout) <= BREAKOUT_NEAR_PCT
                and move is not None and move > BREAKOUT_MOVE_PCT):
            breakout.append((tkr, price, from_breakout, move))

        # Section 3 — notable moves
        if move is not None and abs(move) > NOTABLE_MOVE_PCT:
            notable.append((tkr, price, move, state))

        # Section 4 — held position trim/review (exit/trim framework)
        if tkr in holdings:
            status, reason = positions.assess_position(r.get("channel_zone"), state)
            if status in ("TRIM", "REVIEW"):
                position_flags.append((tkr, price, status, reason, holdings[tkr]))

    # ----- build message -----
    lines = [f"🌅 *Morning Alert — {today}*\n"]

    if high_conv:
        lines.append("*🎯 HIGH CONVICTION IN ENTRY RANGE:*")
        for tkr, price, conv, dist, state in sorted(high_conv, key=lambda x: abs(x[3])):
            lines.append(f"  *{tkr}* ${price:.2f} conv:{conv}/10 "
                         f"{dist:+.1f}% from pullback ({state})"
                         f"{hold_tag(tkr, holdings)}{earn_tag(tkr, earnings)}")
        lines.append("")

    if breakout:
        lines.append("*🚀 BREAKOUT WATCH:*")
        for tkr, price, dist, move in sorted(breakout, key=lambda x: -x[3]):
            lines.append(f"  *{tkr}* ${price:.2f} {dist:+.1f}% from breakout "
                         f"open {move:+.1f}%{hold_tag(tkr, holdings)}{earn_tag(tkr, earnings)}")
        lines.append("")

    if notable:
        lines.append("*📊 NOTABLE MOVES:*")
        for tkr, price, move, state in sorted(notable, key=lambda x: -abs(x[2])):
            icon = "🟢" if move > 0 else "🔴"
            lines.append(f"  {icon} *{tkr}* ${price:.2f} {move:+.1f}% "
                         f"({state}){hold_tag(tkr, holdings)}{earn_tag(tkr, earnings)}")
        lines.append("")

    if position_flags:
        lines.append("*💼 POSITION CHECK:*")
        for tkr, price, status, reason, w in position_flags:
            icon = "✂️" if status == "TRIM" else "⚠️"
            lines.append(f"  {icon} *{tkr}* ${price:.2f} ({w}) {status} — {reason}")
        lines.append("")

    # --- Theme opportunities: each theme's best-entry name within entry range of
    #     its pullback target at the open. Defensive; omitted if none qualify. ---
    theme_opps = []
    try:
        res_by_ticker = dict(zip(df["ticker"], df["resistance"]))
        seen = set()
        for t in theme_engine.get_theme_status()["themes"]:
            be = t.get("best_entry_now")
            if not be or be.get("no_data"):
                continue
            tk = be["ticker"]
            if tk in seen or tk not in snap:
                continue
            price, _ = snap[tk]
            dist = pct(price, res_by_ticker.get(tk))
            if dist is not None and abs(dist) <= ENTRY_RANGE_PCT:
                theme_opps.append((tk, t["name"], be.get("conviction_score"),
                                   be.get("entry_status"), price, dist))
                seen.add(tk)
    except Exception as e:
        print(f"theme opportunities unavailable: {e}")

    if theme_opps:
        lines.append("*🌐 TODAY'S THEME OPPORTUNITIES:*")
        for tk, theme, conv, status, price, dist in theme_opps:
            lines.append(f"  *{tk}* ${price:.2f} {dist:+.1f}% from target — {theme} "
                         f"(conv {conv}/10, {status}){hold_tag(tk, holdings)}")
        lines.append("")

    if not (high_conv or breakout or notable or position_flags or theme_opps):
        lines.append("Nothing actionable this morning.")

    msg = "\n".join(lines).rstrip()
    send(msg)
    print("Morning alert sent.")
    print(msg)


if __name__ == "__main__":
    main()
