import streamlit as st
import pandas as pd
import duckdb
from datetime import date

from sector_map import SECTOR_ETFS, get_constituents
import narrative_alert  # shared briefing logic (generate/save/load) — no forked code
import valuation        # PE / PEG / P-OCF from price + stored TTM inputs
import theme_engine     # secular-trend overlay (coverage, gaps, TLT regime)
import position_sizing  # conviction-led target weights (advisory)
import auto_classify    # CORE vs SPECULATIVE, derived fresh from evidence
import cash_deployment  # speculative stops + thesis alerts + watchlist context
import destination      # Destination Book + cash-aware "next steps" (concentrate & complete)
import diary            # investor action log (append-only, AWS-authoritative)
import holdings_io       # read/write holdings.yaml (logging a trade updates the snapshot)
import manage_universe  # add/remove tickers in the scoring universe
import themes_io        # add/remove a name in the secular-theme map (themes.yaml)
import onboard          # immediate full backfill (price/signals/fundamentals/moat) for new names

st.set_page_config(page_title="Widell Line Dashboard", page_icon="📈", layout="wide")


# ---------------------------------------------------------------------------
# Access control — the dashboard is publicly reachable and shows real holdings,
# so gate the WHOLE app behind a password before any data renders. The secret
# lives in .env (DASHBOARD_PASSWORD); systemd doesn't load .env, so we read it.
# Fail-closed: if no password is configured, the app stays locked.
# ---------------------------------------------------------------------------
def _load_env_file(path=".env"):
    import os
    if os.path.exists(path):
        for line in open(path):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k, v)


def require_auth():
    import os
    import hmac
    _load_env_file()
    expected = os.environ.get("DASHBOARD_PASSWORD")
    if not expected:
        st.title("🔒 Stock Pipeline")
        st.error("Dashboard not configured: set DASHBOARD_PASSWORD in .env, then "
                 "restart Streamlit.")
        st.stop()
    if st.session_state.get("auth_ok"):
        return
    st.title("🔒 Stock Pipeline")
    st.caption("This dashboard is private — enter the password to continue.")
    entered = st.text_input("Password", type="password")
    if entered:
        if hmac.compare_digest(entered, expected):
            st.session_state["auth_ok"] = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    st.stop()


require_auth()

# Section headers the briefing always emits — used to render it nicely in the app.
_BRIEF_HEADERS = ("MARKET CONTEXT", "PORTFOLIO ACTION", "WATCHLIST", "BOTTOM LINE",
                  # legacy headers (older stored briefings) still render cleanly:
                  "ACTIONABLE SETUPS", "WATCH LIST", "PORTFOLIO CHECK")

def briefing_to_markdown(text):
    """Turn the plain-text Telegram briefing into app markdown: the four CAPS
    section headers become bold h5s, '- ' bullets stay as a list."""
    out = []
    for line in text.splitlines():
        s = line.strip()
        if s in _BRIEF_HEADERS:
            out += ["", f"##### {s}"]
        else:
            out.append(line)
    return "\n".join(out)

@st.cache_data(ttl=300)
def load_signals():
    return duckdb.query("""
        WITH latest AS (
            SELECT ticker, date, close, wl_state, wl_flip,
                   regime, composite, conviction_score, rsi_14, dist_52w_high,
                   dist_ma200, ma200, ma50, vsa_label, wl_duration,
                   flip_price, resistance, channel_zone,
                   ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY date DESC) as rn
            FROM 'data/stock_vsa.parquet'
        )
        SELECT ticker, date, ROUND(close,2) as close,
               wl_state, wl_flip, regime, composite, conviction_score,
               ROUND(rsi_14,1) as rsi,
               ROUND(dist_52w_high,1) as dist_52w_hi,
               ROUND(dist_ma200,1) as dist_ma200,
               ROUND(ma200,2) as ma200, ROUND(ma50,2) as ma50,
               CAST(wl_duration AS INT) as days, vsa_label,
               ROUND(flip_price,2) as flip_price,
               ROUND(resistance,2) as key_level,
               CASE
                   WHEN wl_state = 'up' THEN 'pullback'
                   WHEN wl_state = 'inconclusive' THEN 'breakout'
                   ELSE 'resistance'
               END as level_type,
               channel_zone,
               ROUND((close - flip_price) / flip_price * 100, 1) as gap_from_flip
        FROM latest WHERE rn = 1
        ORDER BY composite DESC, wl_state, ticker
    """).df()

@st.cache_data(ttl=300)
def load_rotation():
    import os
    latest = duckdb.query("""
        WITH latest AS (
            SELECT ticker, date, close, wl_state, wl_flip, composite,
                   conviction_score, channel_zone, channel_pos,
                   ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY date DESC) as rn
            FROM 'data/stock_vsa.parquet'
        )
        SELECT ticker, wl_state, wl_flip, composite, conviction_score,
               channel_zone, channel_pos
        FROM latest WHERE rn = 1
    """).df()
    if os.path.exists("data/fundamentals.parquet"):
        fund = pd.read_parquet("data/fundamentals.parquet")[["ticker","fundamental_score"]]
        latest = latest.merge(fund, on="ticker", how="left")
    else:
        latest["fundamental_score"] = pd.NA
    return latest


@st.cache_data(ttl=300)
def load_holdings():
    """holdings.yaml -> {ticker: 'weight'} (incl CASH). Empty dict if absent."""
    import holdings_io
    return holdings_io.load_positions(include_cash=True)


def read_doc(path):
    """Read a markdown doc for display in the app; None if missing/unreadable."""
    import os
    if not os.path.exists(path):
        return None
    try:
        with open(path) as f:
            return f.read()
    except Exception:
        return None


def _log_and_apply(ticker, action, trade_pct, new_weight, recommendation, note=""):
    """Log a trade to the diary AND keep holdings.yaml in sync.

    new_weight (the resulting position size) is written back to holdings.yaml via
    holdings_io.apply_trade, which offsets CASH so the book still sums to 100 — so
    logging a trade is all it takes to keep the snapshot current. Returns a
    one-line confirmation for st.success.
    """
    # Normalize the sign from the action so a TRIM/SELL always reads negative and a
    # BUY/ADD positive, however the amount was typed ("4", "+4", "-4" all work).
    _tp = str(trade_pct).replace("%", "").replace("+", "").strip()
    try:
        _v = abs(float(_tp))
        trade_pct = f"{-_v if action in ('TRIM', 'SELL') else _v:+g}"
    except (ValueError, TypeError):
        pass
    diary.log_action(ticker, action, trade_pct=trade_pct, new_weight=new_weight,
                     recommendation=recommendation, note=note)
    msg = f"Logged {ticker} {action}"
    nw = str(new_weight).replace("%", "").strip()
    if nw:
        try:
            res = holdings_io.apply_trade(ticker, float(nw))
            load_holdings.clear()          # the snapshot changed — drop the cache
            if res:
                msg += (f" → {res['new']:g}% · holdings updated "
                        f"(CASH {res['cash_old']:g}→{res['cash_new']:g}%)")
        except (ValueError, TypeError):
            pass
    return msg


tab_brief, tab_ask, tab_themes, tab_sizing, tab1, tab2, tab3, tab4, tab_manage = st.tabs(
    ["🧭 Briefing", "💬 Ask", "🌐 Themes", "⚖️ Destination", "📊 Signals",
     "📋 Fundamentals", "📖 Guide", "🔄 Rotation", "⚙️ Manage"])

with tab_brief:
    st.title("🧭 Daily Briefing")
    st.caption("Plain-English read on today's signals — the same briefing sent to Telegram "
               "after the close.")

    # Portfolio Intelligence — the cockpit, now driven by the Destination Book:
    # concentrate & complete. One decisive, cash-aware queue (sell the non-core,
    # complete the winners), with the speculative sleeve and stop/thesis context below.
    try:
        _dest = destination.compute_destination()
        _d = cash_deployment.deployment()   # context only: stops, thesis, watchlist

        st.markdown(
            f"#### 🧠 Portfolio Intelligence\n"
            f"**{_dest['n_core']} core** · **{_dest['n_spec']} speculative** · "
            f"**{_dest['n_sell']} to exit** · **{_dest['cash']:.0f}% cash** "
            f"→ **{_dest['pool']:.0f}% to deploy** (cash + sells/reduces, "
            f"keeping a {_dest['reserve']:.0f}% reserve)")
        if _dest.get("macro_wait"):
            st.warning(f"⏸ {_dest['macro_label']} within 3 days — fresh adds held to "
                       "“when cash frees up” until after the print.")

        _ICON = {"SELL": "🔴", "REDUCE": "🟡", "ADD": "🟢"}
        _DACT = {"SELL": "SELL", "REDUCE": "TRIM", "ADD": "ADD"}

        # 🎯 Next Steps — the one ranked, loggable, cash-aware queue.
        if _dest["actions"]:
            st.markdown("##### 🎯 Next Steps — concentrate & complete (act top-down)")
            for _i, a in enumerate(_dest["actions"]):
                dol = (f" · ~${abs(a['suggested_dollars']):,}"
                       if a.get("suggested_dollars") else "")
                ic = _ICON.get(a["type"], "•")
                _nw = a.get("new_weight")
                _to = f" → {_nw:g}%" if _nw is not None else ""
                _part = "  ·  *(partial — rest waits for cash)*" if a.get("partial") else ""
                _txt, _btn = st.columns([6, 1])
                _txt.markdown(f"{ic} **{a['action']} {a['ticker']}** "
                              f"{a['trade_pct']:+g}%{_to}{dol} — {a['detail']}{_part}")
                if _btn.button("✅ Log", key=f"dest_{_i}_{a['ticker']}",
                               help="Log it to your diary and update holdings.yaml to the new weight"):
                    st.success(_log_and_apply(
                        a["ticker"], _DACT[a["type"]], f"{a['trade_pct']:+g}", _nw,
                        f"{a['action']}: {a['detail']}") + " (see ⚙️ Manage).")
            st.caption(f"That's the plan — ~{_dest['uncommitted']:.0f}% left uncommitted, "
                       f"{_dest['reserve']:.0f}% reserve held back. Hold the rest; "
                       "don't chase.")
        else:
            st.info("💵 Book is complete and balanced at target — nothing to do. "
                    "Patience is the edge.")

        # ⏳ When cash frees up — the next steps to complete, once the queue funds.
        if _dest["waitlist"]:
            st.markdown("##### ⏳ When cash frees up — next to complete")
            for w in _dest["waitlist"]:
                st.markdown(f"- **{w['action']} {w['ticker']}** +{w['trade_pct']:g}% → "
                            f"{w['target']:g}% · ⏸ {w.get('wait_reason')} — {w['detail']}")

        # 🟡 Speculative sleeve — held for upside, but on a leash (no thesis exceptions).
        if _dest["spec_keep"]:
            st.markdown("##### 🟡 Speculative sleeve — under a −7% stop")
            st.caption("Not core on the evidence, but kept for upside on a leash. "
                       "Let the stop work; no manual exception.")
            for tk, w in _dest["spec_keep"].items():
                st.markdown(f"- **{tk}** {w:g}%")
        if _dest["pending"]:
            st.caption("⏳ Pending scoring (just onboarded, untouched): "
                       + ", ".join(f"{t} {w:g}%" for t, w in _dest["pending"].items()))

        # 🆕 New ideas — surfaced AFTER the book is complete (don't dilute the queue).
        if _dest.get("deployable", 0) < destination.MIN_ADD and _d.get("validations"):
            with st.expander("🆕 New ideas — once the book is complete"):
                for v in _d["validations"][:6]:
                    st.markdown(f"- **{v['ticker']}** +{v['suggested_pct']:g}% — {v['detail']}")

        # 👀 Watchlist (context) + speculative stop watch + thesis integrity.
        if _d.get("watchlist"):
            st.markdown("##### 👀 Watchlist — not yet actionable")
            for w in _d["watchlist"][:6]:
                wr = f" · ⏸ {w['wait_reason']}" if w.get("wait_reason") else ""
                lbl = f"**{w['action']} {w['ticker']}**" if w.get("action") else f"**{w['ticker']}**"
                st.markdown(f"- {lbl}{wr} — {w['detail']}")

        _watch = [s for s in _d["stops"] if s["dist_to_stop_pct"] <= 3 or s["status"] == "triggered"]
        if _watch:
            st.markdown("##### ⚠️ Speculative stop watch")
            for s in _watch:
                tag = "🛑 STOP HIT" if s["status"] == "triggered" else "watch"
                st.markdown(f"- **{s['ticker']}** ${s['current']} — stop ${s['stop']} "
                            f"({s['dist_to_stop_pct']}% away) — {tag}")

        if _d["thesis_alerts"]:
            for a in _d["thesis_alerts"]:
                st.warning(f"⚠️ {a['ticker']}: {a['detail']}")
    except Exception as _e:
        st.caption(f"Portfolio Intelligence unavailable: {_e}")
    st.divider()

    # Read-only by design: this dashboard is publicly reachable, so it must not
    # expose any control that triggers a Claude API call on our key. The briefing
    # is generated server-side by the trusted close cron (narrative_alert.py) and
    # only displayed here. An on-demand "regenerate" / interactive Q&A will come
    # later, behind authentication.
    brief = narrative_alert.load_briefing()
    if brief:
        st.markdown(f"**As of {brief.get('date','?')}** "
                    f"· generated {brief.get('generated_at','?').replace('T',' ')}")
        st.markdown(briefing_to_markdown(brief.get("narrative", "")))
    else:
        st.info("No briefing yet. It's generated automatically after the close "
                "pipeline each weekday — check back after 4:30 PM ET.")

with tab_ask:
    st.title("💬 Ask")
    st.caption("Ask about any holding, candidate, or your portfolio. Answers use the "
               "same signal stack as the daily briefing (Widell state, conviction, tier, "
               "moat, valuation, theme, cash-deployment) — there's no news feed, so it'll "
               "say when it can't see a catalyst. Each question calls Claude.")

    import qa_engine
    if "qa_history" not in st.session_state:
        st.session_state["qa_history"] = []

    for _role, _content, _tks in st.session_state["qa_history"]:
        with st.chat_message(_role):
            st.markdown(_content)
            if _role == "assistant" and _tks:
                st.caption("context: " + ", ".join(_tks))

    _q = st.chat_input("e.g. 'thoughts on GEV today?' or 'where should my cash go?'")
    if _q:
        st.session_state["qa_history"].append(("user", _q, []))
        with st.chat_message("user"):
            st.markdown(_q)
        with st.chat_message("assistant"):
            with st.spinner("Reading the signals…"):
                try:
                    _ans, _tks = qa_engine.answer_question(_q)
                except Exception as _e:
                    _ans, _tks = f"Sorry — couldn't answer that right now ({_e}).", []
            st.markdown(_ans)
            if _tks:
                st.caption("context: " + ", ".join(_tks))
        st.session_state["qa_history"].append(("assistant", _ans, _tks))

with tab_themes:
    st.title("🌐 Secular Themes")
    st.caption("Your secular-trend map overlaid on live signals — coverage, gaps, "
               "best entries. ⭐ = wide moat + reasonable valuation (your profile).")

    status = theme_engine.get_theme_status()
    cov    = theme_engine.get_portfolio_theme_coverage()
    regime = status["tlt_regime"]

    # --- Section 1: TLT regime banner ---
    banner = f"{regime['icon']} {regime['label']}"
    (st.success if regime["signal"] == "tailwind"
     else st.error if regime["signal"] == "headwind"
     else st.warning)(banner)

    # --- Section 2: portfolio theme coverage ---
    c1, c2, c3 = st.columns(3)
    c1.metric("Themes covered", f"{cov['themes_covered']} / {cov['total_themes']}")
    c2.metric("Positions", cov["held_count"],
              help=f"target {cov['target_min']}–{cov['target_max']}")
    c3.metric("Concentrated themes", len(cov["concentrated"]))
    if cov["gaps"]:
        st.markdown("**Gaps (no exposure):** " + ", ".join(g["name"] for g in cov["gaps"]))
    if cov["concentrated"]:
        st.markdown("**Concentrated (3+):** " + "; ".join(
            f"{c['name']} ({', '.join(c['held_names'])})" for c in cov["concentrated"]))
    if cov["unthemed_holdings"]:
        st.markdown("**Off-thesis holdings (in no theme):** " + ", ".join(
            u["ticker"] + (f" ({u['note']})" if u["note"] else "")
            for u in cov["unthemed_holdings"]))
    st.divider()

    # --- Section 3: theme cards (regime shown as the banner above) ---
    _conv_badge = {"high": "🟢 HIGH", "medium": "🟡 MEDIUM", "low": "⚪ LOW"}

    def _name_line(n):
        if n.get("no_data"):
            held = f" · 💼 {n['held']}" if n.get("held") else ""
            return f"- **{n['ticker']}** — no signal data{held}"
        badges = []
        if n.get("held"):         badges.append(f"💼 HELD {n['held']}")
        if n.get("fits_profile"): badges.append("⭐")
        moat = f"moat {n['moat_rating']}/5" if n.get("moat_rating") else "moat n/a"
        vlab = n.get("val_label") or "val n/a"
        tail = ("  ·  " + " ".join(badges)) if badges else ""
        return (f"- **{n['ticker']}** — {n['entry_status']} · conv "
                f"{n.get('conviction_score')}/10 · {n.get('channel_zone')} · "
                f"{moat} · {vlab}{tail}")

    for t in status["themes"]:
        if t["is_regime"]:
            continue
        with st.container(border=True):
            st.markdown(f"### {t['name']}  ·  {_conv_badge.get(t['conviction'], t['conviction'])}")
            st.caption(t["thesis"])
            if t["theme_gap"]:
                st.markdown("⚠️ **GAP — no exposure in this theme**")

            st.markdown("**Best in class:**")
            for n in t["best_in_class"]:
                st.markdown(_name_line(n))

            be = t["best_entry_now"]
            if be and not be.get("no_data"):
                star = " ⭐" if be.get("fits_profile") else ""
                st.markdown(f"🎯 **Best entry now:** {be['ticker']} — {be['entry_status']}, "
                            f"conv {be.get('conviction_score')}/10, {be.get('channel_zone')}{star}")
            if t["held_names"]:
                st.markdown(f"💼 **Held:** {', '.join(t['held_names'])}")

            with st.expander(f"All {len(t['names'])} names"):
                for n in t["names"]:
                    st.markdown(_name_line(n))

            st.caption(f"⚠️ {t['constraint']}")

with tab_sizing:
    st.title("⚖️ Destination Book")
    st.caption("The portfolio you're **building toward** — your highest-conviction names "
               "at full target weights (conviction-led, capped at 15%, holding an "
               f"{destination.CASH_RESERVE:.0f}% reserve). Read-only: every move toward it "
               "lives on the 🧭 Briefing. *current → target* is the map; the Briefing is "
               "the next step.")

    _dst = destination.compute_destination()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Core names", _dst["n_core"])
    c2.metric("Cash now", f"{_dst['cash']:.0f}%")
    c3.metric("To deploy", f"{_dst['pool']:.0f}%", help="cash + sell/reduce proceeds")
    c4.metric("Reserve", f"{_dst['reserve']:.0f}%")
    st.divider()

    st.subheader("Core — current → target")
    st.caption("Conviction is the driver. 🟢 below target (complete it) · 🔴 above · "
               "⭐ = wide moat + reasonable valuation.")
    bk = pd.DataFrame(_dst["book"])
    if len(bk):
        bk["⭐"] = bk["fits_profile"].map(lambda b: "⭐" if b else "")
        bk = bk[["ticker", "current", "target", "delta", "conviction",
                 "moat_rating", "val_label", "entry_status", "⭐"]].rename(
            columns={"current": "current %", "target": "target %", "delta": "Δ to target",
                     "moat_rating": "moat", "val_label": "val", "entry_status": "entry"})

        def _c_delta(v):
            try:
                v = float(v)
            except (TypeError, ValueError):
                return ""
            return ("color:#00cc44;font-weight:bold" if v >= 0.5
                    else "color:#ff6666" if v <= -0.5 else "color:#888")

        st.dataframe(bk.style.map(_c_delta, subset=["Δ to target"]),
                     use_container_width=True, hide_index=True)
    else:
        st.info("No core holdings found.")

    if _dst["spec_keep"] or _dst["sells"] or _dst["pending"]:
        cols = st.columns(3)
        cols[0].markdown("**🟡 Spec sleeve** (−7% stop)\n\n" +
                         ("\n".join(f"- {t} {w:g}%" for t, w in _dst["spec_keep"].items())
                          or "_none_"))
        cols[1].markdown("**🔴 Exit** (non-core)\n\n" +
                         ("\n".join(f"- {t} {w:g}%" for t, w in _dst["sells"].items())
                          or "_none_"))
        cols[2].markdown("**⏳ Pending** (no score yet)\n\n" +
                         ("\n".join(f"- {t} {w:g}%" for t, w in _dst["pending"].items())
                          or "_none_"))

    st.caption("Informational only — to act, use the 🧭 Briefing (the cash-aware next "
               "steps). Not financial advice.")

with tab1:
    st.title("📈 Widell Line Signal Dashboard")
    st.caption(f"Data as of {date.today()}")
    df = load_signals()
    holdings = load_holdings()
    df["held"] = df["ticker"].map(holdings).fillna("")

    c1,c2,c3,c4,c5,c6 = st.columns(6)
    c1.metric("🟢 Up",           (df["wl_state"]=="up").sum())
    c2.metric("🟡 Inconclusive",  (df["wl_state"]=="inconclusive").sum())
    c3.metric("🔴 Down",         (df["wl_state"]=="down").sum())
    c4.metric("⚡ Flips Today",   int(df["wl_flip"].sum()))
    c5.metric("🔥 High Score ≥2", (df["composite"]>=2).sum())
    c6.metric("🎯 Conviction ≥8", (df["conviction_score"]>=8).sum())
    st.divider()

    # --- High Conviction callout — first thing the user sees ---
    import os as _os_hc
    st.subheader("🎯 High Conviction — Conviction ≥ 8")
    hc = df[df["conviction_score"] >= 8].copy()
    if _os_hc.path.exists("data/fundamentals.parquet"):
        _fund_hc = pd.read_parquet("data/fundamentals.parquet")[["ticker","fundamental_score"]]
        hc = hc.merge(_fund_hc, on="ticker", how="left")
    else:
        hc["fundamental_score"] = pd.NA
    if len(hc) > 0:
        hc = hc.sort_values("conviction_score", ascending=False)
        for _, row in hc.iterrows():
            icon  = "🟢" if row["wl_state"]=="up" else "🔴" if row["wl_state"]=="down" else "🟡"
            gap   = f"{row['gap_from_flip']:+.1f}%" if pd.notna(row["gap_from_flip"]) else "N/A"
            pb    = f"{row['level_type']}→${row['key_level']:.2f}" if pd.notna(row["key_level"]) else "N/A"
            f_str = f"F:{int(row['fundamental_score'])}/5" if pd.notna(row.get("fundamental_score")) else "F:N/A"
            zone  = row["channel_zone"] if pd.notna(row["channel_zone"]) else "—"
            held  = f" | 💼 **HELD {row['held']}**" if row.get("held") else ""
            st.markdown(
                f"**{row['ticker']}** {icon} {row['wl_state'].upper()} "
                f"| Conv: **{int(row['conviction_score'])}/10** "
                f"| Score: **{int(row['composite'])}** "
                f"| {f_str} "
                f"| Zone: {zone} "
                f"| Gap from flip: **{gap}** "
                f"| Pullback target: **{pb}**"
                f"{held}"
            )
    else:
        st.info("No high conviction setups today.")
    st.divider()

    flips = df[df["wl_flip"]==True]
    if len(flips) > 0:
        st.subheader("⚡ Flips Today — Action Items")
        for _, row in flips.iterrows():
            icon = "🟢" if row["wl_state"]=="up" else "🔴" if row["wl_state"]=="down" else "🟡"
            gap  = f"{row['gap_from_flip']:+.1f}%" if pd.notna(row["gap_from_flip"]) else "N/A"
            pb   = f"{row['level_type']}→${row['key_level']:.2f}" if pd.notna(row["key_level"]) else "N/A"
            st.markdown(
                f"**{row['ticker']}** {icon} {row['wl_state'].upper()} "
                f"| Score: **{int(row['composite'])}** "
                f"| RSI: {row['rsi']} "
                f"| Regime: {row['regime']} "
                f"| Days: {int(row['days'])} "
                f"| Gap from flip: **{gap}** "
                f"| Pullback target: **{pb}** "
                f"| {row['vsa_label']}"
            )
        st.divider()



    # Combined conviction view
    import os as _os
    if _os.path.exists("data/fundamentals.parquet"):
        fund_data = pd.read_parquet("data/fundamentals.parquet")[
            ["ticker","fundamental_score","rev_growth_yoy","gross_margin"]
        ]
        combined = df.merge(fund_data, on="ticker", how="left")
        up_combined = combined[combined["wl_state"]=="up"].copy()
        if len(up_combined) > 0:
            st.subheader("🎯 Combined Signal — Up State")
            for _, row in up_combined.iterrows():
                w_score = int(row["composite"])
                f_score = int(row["fundamental_score"]) if pd.notna(row.get("fundamental_score")) else None
                gap_v   = row["gap_from_flip"] if pd.notna(row["gap_from_flip"]) else 0
                zone    = row["channel_zone"] if pd.notna(row["channel_zone"]) else ""
                chase   = "🔴 CHASING+EXT" if gap_v > 5 and zone=="extended" else                           "🔴 CHASING"    if gap_v > 5 else                           "🟡 ELEVATED"   if gap_v > 2 else                           "🟢 AT ENTRY"
                f_str   = f"F:{f_score}/5" if f_score is not None else "F:N/A"
                days    = int(row["days"]) if pd.notna(row["days"]) else 0
                conv    = int(row["conviction_score"]) if pd.notna(row.get("conviction_score")) else 0
                pb      = f"pb→${row['key_level']:.2f}" if pd.notna(row.get("key_level")) else ""
                st.markdown(
                    f"**{row['ticker']}** {chase} "
                    f"| Score: **{w_score}** | Conv: **{conv}/10** | {f_str} "
                    f"| {zone} | {pb} | Days: {days}"
                )
            st.divider()

    st.subheader("🔍 Full Universe")
    c1,c2,c3 = st.columns(3)
    sf = c1.multiselect("State",   ["up","inconclusive","down"], default=["up","inconclusive","down"])
    rf = c2.multiselect("Regime",  ["bull","mixed","bear"],      default=["bull","mixed","bear"])
    ms = c3.slider("Min Score", -6, 6, -6)

    filt = df[df["wl_state"].isin(sf) & df["regime"].isin(rf) & (df["composite"]>=ms)]

    def cs(v):
        if v=="up":           return "background-color:#1a472a;color:white"
        if v=="down":         return "background-color:#6b1a1a;color:white"
        if v=="inconclusive": return "background-color:#4a3800;color:white"
        return ""
    def cr(v):
        return "color:#00cc44" if v=="bull" else "color:#ff4444" if v=="bear" else "color:#ffaa00"
    def csc(v):
        if v>=3:  return "color:#00ff88;font-weight:bold"
        if v>=1:  return "color:#88ff88"
        if v<=-3: return "color:#ff4444;font-weight:bold"
        if v<=-1: return "color:#ff8888"
        return ""
    def cgap(v):
        if pd.isna(v): return ""
        if v>5:  return "color:#ff4444;font-weight:bold"
        if v>2:  return "color:#ffaa00"
        return "color:#00cc44"
    def ccv(v):
        if pd.isna(v): return ""
        if v>=8: return "background-color:#1a472a;color:white;font-weight:bold"
        if v>=6: return "color:#00ff88;font-weight:bold"
        if v>=4: return "color:#88ff88"
        return ""

    cols = ["ticker","held","close","wl_state","regime","composite","conviction_score","rsi",
            "dist_52w_hi","dist_ma200","ma200","ma50","days",
            "gap_from_flip","key_level","level_type","vsa_label"]
    st.dataframe(
        filt[cols].style
            .map(cs,   subset=["wl_state"])
            .map(cr,   subset=["regime"])
            .map(csc,  subset=["composite"])
            .map(ccv,  subset=["conviction_score"])
            .map(cgap, subset=["gap_from_flip"]),
        use_container_width=True, height=600)

    st.divider()
    st.subheader("📊 Score Distribution")
    st.bar_chart(df["composite"].value_counts().sort_index())

    st.divider()
    st.subheader("🔎 Ticker History")
    ticker = st.selectbox("Select ticker", sorted(df["ticker"].unique()))
    hist = duckdb.query(f"""
        SELECT date, ROUND(close,2) as close, wl_state, regime,
               composite, ROUND(rsi_14,1) as rsi, vsa_label,
               wl_flip, ROUND(flip_price,2) as flip_price,
               ROUND(resistance,2) as key_level,
               ROUND(reg_center,2) as reg_center,
               ROUND(reg_upper,2) as reg_upper,
               ROUND(reg_lower,2) as reg_lower,
               channel_zone
        FROM 'data/stock_vsa.parquet'
        WHERE ticker='{ticker}' ORDER BY date DESC LIMIT 90
    """).df().sort_values("date")

    st.markdown("**Price with 200-day Regression Channel**")
    channel_df = hist.set_index("date")[["close","reg_upper","reg_center","reg_lower"]].dropna()
    st.line_chart(channel_df, height=300)

    latest_zone = hist.iloc[-1]["channel_zone"] if len(hist) > 0 else ""
    latest_pos  = hist.iloc[-1]["close"]
    st.caption(f"Current channel zone: **{latest_zone}** | Close: ${latest_pos:.2f}")

    c1,c2 = st.columns(2)
    c1.line_chart(hist.set_index("date")["composite"], height=200)
    c2.line_chart(hist.set_index("date")["rsi"], height=200)

    st.dataframe(hist[["date","close","wl_state","channel_zone","composite","rsi","vsa_label","wl_flip"]],
                 use_container_width=True, height=250)
with tab2:
    st.title("📋 Fundamental Scores")
    st.caption("Sector-aware 0-5 score: each name graded by the rubric for its business "
               "archetype (software / platform / bank / energy / industrial / staple / "
               "pre-profit) — banks on ROE & efficiency, energy on ROE & cash flow, not "
               "software margins. Forward PE is our own run-rate projection (base = median).")

    import os
    if os.path.exists("data/fundamentals.parquet"):
        fund = pd.read_parquet("data/fundamentals.parquet")

        # Moat scores (qualitative, from moat_score.py) — optional join.
        has_moat = os.path.exists("data/moat.parquet")
        if has_moat:
            moat = pd.read_parquet("data/moat.parquet")[
                ["ticker", "moat_rating", "moat_type", "moat_summary", "moat_risk"]
            ]
            fund = fund.merge(moat, on="ticker", how="left")

        # Valuation (PE / PEG / P-OCF) — computed from current price + stored TTM
        # inputs. Context only, not part of conviction. Present only if the inputs
        # exist in fundamentals.parquet (fetch_fundamentals.py populates them).
        has_val = all(c in fund.columns for c in ("ttm_eps", "ttm_ocf", "shares"))
        if has_val:
            prices = load_signals()[["ticker", "close"]]
            fund = fund.merge(prices, on="ticker", how="left")
            vals = fund.apply(lambda r: valuation.compute_valuation(r.get("close"), r), axis=1)
            fund["PE"]    = [v["pe"]    for v in vals]
            fund["PEG"]   = [v["peg"]   for v in vals]
            fund["P/OCF"] = [v["p_ocf"] for v in vals]
            fwd = fund.apply(lambda r: valuation.compute_forward(r.get("close"), r), axis=1)
            fund["fwd PE"] = [f["fwd_pe_base"] for f in fwd]

        # Summary metrics
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Score 5 (Elite)",    (fund["fundamental_score"]==5).sum())
        c2.metric("Score 4 (Strong)",   (fund["fundamental_score"]==4).sum())
        c3.metric("Score 3 (Good)",     (fund["fundamental_score"]==3).sum())
        c4.metric("Score ≤2 (Weak)",    (fund["fundamental_score"]<=2).sum())
        st.divider()

        # Filter
        min_f = st.slider("Min Fundamental Score", 0, 5, 0)
        filtered = fund[fund["fundamental_score"] >= min_f].copy()

        def color_fscore(v):
            if v == 5: return "background-color:#1a472a;color:white"
            if v == 4: return "background-color:#2d5a1b;color:white"
            if v == 3: return "color:#88ff88"
            if v <= 1: return "color:#ff8888"
            return ""

        def color_moat(v):
            if pd.isna(v): return ""
            if v >= 5: return "background-color:#1a472a;color:white;font-weight:bold"
            if v == 4: return "color:#00ff88;font-weight:bold"
            if v == 3: return "color:#88ff88"
            if v <= 2: return "color:#ff8888"
            return ""

        display_cols = ["ticker","fundamental_score"]
        if "archetype" in filtered.columns:
            display_cols += ["archetype"]
        if has_moat:
            display_cols += ["moat_rating","moat_type"]
        if has_val:
            display_cols += ["PE","PEG","P/OCF","fwd PE"]
        _extra = [c for c in ["rev_growth_yoy","op_margin","roe","efficiency_ratio",
                              "operating_cf_B","as_of"] if c in filtered.columns]
        display_cols += _extra
        styler = filtered[display_cols].style.map(color_fscore, subset=["fundamental_score"])
        if has_moat:
            styler = styler.map(color_moat, subset=["moat_rating"])
        st.dataframe(styler, use_container_width=True, height=600)

        # Per-name moat detail (summary + key risk) for names with a moat score.
        if has_moat:
            st.divider()
            st.subheader("🏰 Moat Detail")
            moat_named = filtered.dropna(subset=["moat_rating"]).sort_values(
                "moat_rating", ascending=False)
            if len(moat_named):
                pick = st.selectbox("Ticker", moat_named["ticker"].tolist(),
                                    key="moat_pick")
                r = moat_named[moat_named["ticker"] == pick].iloc[0]
                st.markdown(
                    f"**{pick}** — Moat **{int(r['moat_rating'])}/5** "
                    f"({r['moat_type']})\n\n"
                    f"**Summary:** {r['moat_summary']}\n\n"
                    f"**Key risk:** {r['moat_risk']}"
                )
            else:
                st.info("No moat scores for the current filter. Run moat_score.py.")

        st.divider()
        st.subheader("Score Methodology")
        st.markdown("""
| Metric | Threshold | Points |
|---|---|---|
| Revenue growth YoY | > 20% | +1 |
| Gross margin | > 50% | +1 |
| Operating margin | > 15% | +1 |
| EPS growth YoY | > 10% | +1 |
| Operating cash flow | Positive | +1 |

Score 5 = elite. Score 0-1 = avoid or speculative.
ETFs and some international tickers (ASML, TSM, ARM) have no fundamental data.
        """)
    else:
        st.warning("No fundamentals data found. Run fetch_fundamentals.py first.")

with tab3:
    st.title("📖 Dashboard Guide")
    st.caption("How to read and use the Widell Line Signal Dashboard")

    # Official spec — what the system is for and how its risks are managed.
    _obj = read_doc("docs/KEY_OBJECTIVES.md")
    with st.expander("🎯 Key Objectives — what this system is for"):
        st.markdown(_obj if _obj else "_docs/KEY_OBJECTIVES.md not found_")
    _thesis = read_doc("docs/INVESTMENT_THESIS.md")
    with st.expander("📜 Investment Thesis — secular trends white paper"):
        st.markdown(_thesis if _thesis else "_docs/INVESTMENT_THESIS.md not found_")
    _risk = read_doc("docs/MODEL_RISK.md")
    with st.expander("🛡️ Model Risk Monitoring — known concerns & controls"):
        st.markdown(_risk if _risk else "_docs/MODEL_RISK.md not found_")
    _bt = read_doc("docs/CONVICTION_BACKTEST.md")
    with st.expander("🔬 Conviction Backtest — honest validation of the score"):
        st.markdown(_bt if _bt else "_docs/CONVICTION_BACKTEST.md not found_")
    st.divider()

    st.header("The Six Tabs")
    st.markdown("""
| Tab | What it's for |
|---|---|
| 🧭 **Briefing** | The plain-English daily read (same as the Telegram briefing): a 🧠 Portfolio Intelligence cockpit driven by the Destination Book — one cash-aware **Next Steps** queue (concentrate & complete: sell the non-core, complete the winners), the speculative sleeve under its stop, what's next when cash frees up, plus the stop watch and the LLM market read. Generated server-side after the close. |
| 💬 **Ask** | Ask about any holding, candidate, or your portfolio in plain English — answers reuse the same signal stack (Widell, conviction, tier, moat, valuation, theme, deployment). Signals only: no news feed, so it says when it can't see a catalyst. Each question calls Claude (behind the password). |
| 🌐 **Themes** | Your secular-trend map: TLT bond-regime banner, theme coverage vs gaps, over-concentration, off-thesis holdings, and the best entry per theme. The best opportunities to act on within each theme — informational, not directives. |
| ⚖️ **Destination** | The book you're building toward — your highest-conviction names at full target weights (current → target), plus the spec sleeve, the exit list, and pending names. **No actions here** — the Briefing is the next step toward it. |
| 📊 **Signals** | The full signal stack: High Conviction callout, flips, up-state entry analysis, and the filterable full universe. |
| 📋 **Fundamentals** | F score (0-5), moat rating (1-5) + per-name detail, and valuation (PE / PEG / P-OCF). |
| 📖 **Guide** | This page — objectives, model risk, and how to read everything. |
| 🔄 **Rotation** | Top-down sector/ETF ranking + constituent laggard scan. |
| ⚙️ **Manage** | Add/remove companies in the scoring universe — adding maps the name to your secular theme(s) and immediately backfills everything (price, signals, fundamentals, moat; ~2-3 min) — and keep an investor diary — log the actions you actually took (date, ticker, action, trade %, new weight, recommendation). Logging writes the new weight into holdings.yaml automatically. Use the ✅ Log buttons on Briefing to capture a recommendation you executed. |
""")

    st.divider()
    st.header("Quality & Context Signals")
    st.markdown("""
These layers add quality, valuation, theme, and macro context. **Moat, valuation,
and themes inform the read but do NOT change the conviction score.**

- **Moat rating (1-5)** — durability of the competitive advantage (Claude, quarterly). 4-5 = wide moat; pullbacks in wide-moat names are more forgiving.
- **Valuation (PE / PEG / P-OCF)** — *context, not part of conviction.* P-OCF is a free-cash-flow proxy (Polygon doesn't expose capex). A wide-moat compounder can deserve a premium; watch a stretched PEG on thinner moats.
- **🗓️ Earnings flag** — a name reports within 7 days; a reason to wait on an entry.
- **💼 HELD** — a current holding (from holdings.yaml); CASH is dry powder to deploy.
- **TLT bond regime** — macro gauge: TLT up = yields falling = growth tailwind; down = headwind.
- **⭐ Fits profile** — wide moat + reasonable valuation in a future-facing theme: the ideal name.
- **Position check (TRIM / REVIEW / HOLD)** — held names that are extended (trim) or breaking down (review). No hard stops — long-term framing.
""")

    st.divider()
    st.header("What is the Widell Line?")
    st.markdown("The **Widell Line** is an original empirical swing-structure state machine built from first principles and validated across 6 years of daily data. It tracks resistance (swing highs) and support (swing lows) using a confirmed-optimal N=3 bar window, scored daily across a 99-ticker universe.")

    st.divider()
    st.header("The Three States")
    c1,c2,c3 = st.columns(3)
    c1.markdown("### 🟢 Up\nPrice **above resistance**. Buyers in control.\n\n**5-day avg: +2.38%**\n\n*Consider entry if score ≥ 2 and top-down aligned.*")
    c2.markdown("### 🟡 Inconclusive\nPrice **between support and resistance**. No trend.\n\n**5-day avg: +0.95%**\n\n*Hold existing. Wait for flip to up.*")
    c3.markdown("### 🔴 Down\nPrice **below support**. Sellers in control.\n\n**5-day avg: -0.83%**\n\n*Avoid entries. Reduce if score ≤ -3 and bear.*")

    st.divider()
    st.header("Gap from Flip & Pullback Target")
    st.markdown("""
The **Gap from Flip** shows how far price has moved since the Widell Line flipped to its current state.
This tells you whether you are entering at the signal or chasing a move.

| Gap | Status | Action |
|---|---|---|
| < 2% | 🟢 AT ENTRY | Signal is fresh, entry zone |
| 2-5% | 🟡 ELEVATED | Elevated risk, consider waiting |
| > 5% | 🔴 CHASING | Wait for pullback to target |

The **Pullback Target** is the resistance level that was broken when price flipped to up.
This is where old resistance becomes new support — the ideal re-entry zone after a gap.

**Example:** AMAT flips to up at $450. Gaps to $492 (+9.4%).
Pullback target is $448. Wait for price to retrace to $448,
confirm it holds as support, then enter.
    """)

    st.divider()
    st.header("Composite Score (-6 to +6)")
    st.markdown("""
| Component | Range | What it measures |
|---|---|---|
| Widell state | +2/0/-2 | Price vs swing levels |
| Widell flip | +1/0/-1 | State just changed |
| VSA label | +2 to -2 | Volume spread bar type |
| MA regime | +1/0/-1 | Bull/mixed/bear alignment |

**+4 to +6:** Strong buy | **+2 to +3:** Consider entry | **0 to +1:** Neutral | **-1 to -2:** Caution | **-3 to -6:** Avoid
    """)

    st.divider()
    st.header("Conviction Score (0 to 10)")
    st.markdown("""
A buy-zone quality score that blends *where* price sits, *what* you'd own, and *timing*.

| Component | Range | Scoring |
|---|---|---|
| Channel position | 0-4 | lower 4 · middle 3 · breakdown 2 · upper 1 · unknown 1 · extended 0 |
| Fundamentals | 0-3 | F5 → 3 · F4 → 2 · F3 → 1 · F0-2 → 0 |
| Widell state | 0-2 | up 2 · inconclusive 1 · down 0 |
| Flip recency | 0-1 | flipped within last 5 bars → 1 |

**8-10:** Highest-conviction buy zone | **6-7:** Watch closely | **≤5:** Lower conviction.
Unlike composite (momentum/signal direction), conviction rewards buying quality names *low in their channel*.
    """)

    st.divider()
    st.header("Entry Checklist")
    st.markdown("""
- ✅ Widell state = up
- ✅ Composite score ≥ 2
- ✅ Gap from flip < 2% (or wait for pullback to target)
- ✅ SPY not in down state
- ✅ Sector ETF not in down state
- ✅ Regime = bull or mixed
- ✅ RSI not above 75
    """)

    st.divider()
    st.header("Exit / Reduce Checklist")
    st.markdown("""
- 🚨 State flips to down AND score ≤ -3 AND regime = bear
- 🚨 Drawdown from peak exceeds 35%
- 🚨 Sector ETF flips to down
    """)

    st.divider()
    st.header("Column Reference")
    st.markdown("""
| Column | Description |
|---|---|
| ticker | Stock symbol |
| close | Latest closing price |
| wl_state | up / inconclusive / down |
| regime | bull / mixed / bear |
| composite | Signal score -6 to +6 |
| conviction_score | Buy-zone quality 0 to 10 (8+ = highest conviction) |
| rsi | 14-day RSI |
| dist_52w_hi | % below 52-week high |
| dist_ma200 | % above/below 200-day MA |
| ma200 | 200-day MA price |
| ma50 | 50-day MA price |
| days | Days in current state |
| gap_from_flip | % move since flip (green<2%, yellow 2-5%, red>5%) |
| key_level | Key price level: pullback target (up), breakout level (inconclusive), resistance (down) |
| vsa_label | VSA bar classification |
| held | Your current weight in this name (from holdings.yaml), blank if not held |
| fundamental_score | Business quality 0-5 |
| moat_rating | Competitive-moat durability 1-5 (Fundamentals tab) |
| PE / PEG / P-OCF | Valuation — context only, not part of conviction (Fundamentals tab) |
    """)

    st.divider()
    st.caption("Built by Spencer Widell | github.com/spencerwidell/stock-pipeline | Not financial advice.")

with tab4:
    st.title("🔄 Sector Rotation")
    st.caption(f"Data as of {date.today()} — rank sectors by opportunity, then find quality laggards within them")

    rot = load_rotation()

    STATE_ICON = {"up": "🟢", "inconclusive": "🟡", "down": "🔴"}
    STATE_RANK = {"up": 0, "inconclusive": 1, "down": 2}
    MIN_FUND = 3

    # ----------------------------------------------------------------------
    # Section A — ETF / sector ranking
    # ----------------------------------------------------------------------
    st.subheader("Section A — Sector / Thematic ETF Ranking")
    st.caption("Best opportunity (favorable state + lower channel) at top")

    etf = rot[rot["ticker"].isin(SECTOR_ETFS)].copy()
    etf["state_rank"] = etf["wl_state"].map(STATE_RANK).fillna(3)
    etf = etf.sort_values(["state_rank", "channel_pos"], na_position="last").reset_index(drop=True)
    etf["state"] = etf["wl_state"].map(STATE_ICON).fillna("?") + " " + etf["wl_state"].astype(str)

    etf_view = etf[["ticker","state","composite","channel_zone","channel_pos"]].rename(
        columns={"state":"wl_state"})

    def cs_state(v):
        if "up" in str(v):           return "background-color:#1a472a;color:white"
        if "down" in str(v):         return "background-color:#6b1a1a;color:white"
        if "inconclusive" in str(v): return "background-color:#4a3800;color:white"
        return ""
    def csc(v):
        if pd.isna(v): return ""
        if v>=3:  return "color:#00ff88;font-weight:bold"
        if v>=1:  return "color:#88ff88"
        if v<=-3: return "color:#ff4444;font-weight:bold"
        if v<=-1: return "color:#ff8888"
        return ""
    def czone(v):
        if v=="lower":     return "color:#00ff88;font-weight:bold"
        if v=="middle":    return "color:#88ff88"
        if v=="extended":  return "color:#ff4444;font-weight:bold"
        if v=="upper":     return "color:#ffaa00"
        return ""

    st.dataframe(
        etf_view.style
            .map(cs_state, subset=["wl_state"])
            .map(csc,      subset=["composite"])
            .map(czone,    subset=["channel_zone"])
            .format({"channel_pos": "{:.3f}"}, na_rep="n/a"),
        use_container_width=True, height=600)

    st.divider()

    # ----------------------------------------------------------------------
    # Section B — constituent laggard scan
    # ----------------------------------------------------------------------
    st.subheader("Section B — Constituent Laggard Scan")
    st.caption(f"For favorable ETFs (up state or lower/middle zone): F ≥ {MIN_FUND} constituents "
               "with more room to run than their sector, or lagging its momentum")

    by_ticker = rot.set_index("ticker")
    favorable = etf[(etf["wl_state"]=="up") | (etf["channel_zone"].isin(["lower","middle"]))]

    laggards = []
    for _, e in favorable.iterrows():
        etf_tkr, etf_state, etf_cpos = e["ticker"], e["wl_state"], e["channel_pos"]
        for stock in get_constituents(etf_tkr):
            if stock not in by_ticker.index:
                continue
            s = by_ticker.loc[stock]
            f_score = s["fundamental_score"]
            if pd.isna(f_score) or f_score < MIN_FUND:
                continue
            s_cpos, s_state = s["channel_pos"], s["wl_state"]
            room_to_run = pd.notna(s_cpos) and pd.notna(etf_cpos) and s_cpos < etf_cpos
            lagging = etf_state == "up" and s_state in ("inconclusive", "down")
            if not (room_to_run or lagging):
                continue
            tag = "BOTH" if room_to_run and lagging else "ROOM_TO_RUN" if room_to_run else "LAGGING"
            laggards.append({
                "ticker": stock, "sector_etf": etf_tkr, "tag": tag,
                "fundamental_score": int(f_score), "channel_zone": s["channel_zone"],
                "channel_pos": s_cpos, "conviction_score": s["conviction_score"],
            })

    if laggards:
        lag_df = pd.DataFrame(laggards).sort_values(
            "channel_pos", na_position="last").reset_index(drop=True)
        lag_view = lag_df[["ticker","sector_etf","tag","fundamental_score",
                           "channel_zone","conviction_score","channel_pos"]]

        def ctag(v):
            if v=="BOTH":        return "background-color:#1a472a;color:white;font-weight:bold"
            if v=="ROOM_TO_RUN": return "color:#00ff88"
            if v=="LAGGING":     return "color:#ffaa00"
            return ""
        def cf(v):
            if pd.isna(v): return ""
            if v==5: return "background-color:#1a472a;color:white"
            if v==4: return "background-color:#2d5a1b;color:white"
            if v==3: return "color:#88ff88"
            return ""
        def ccv(v):
            if pd.isna(v): return ""
            if v>=8: return "background-color:#1a472a;color:white;font-weight:bold"
            if v>=6: return "color:#00ff88;font-weight:bold"
            if v>=4: return "color:#88ff88"
            return ""

        st.dataframe(
            lag_view.style
                .map(ctag,  subset=["tag"])
                .map(cf,    subset=["fundamental_score"])
                .map(czone, subset=["channel_zone"])
                .map(ccv,   subset=["conviction_score"])
                .format({"channel_pos": "{:.3f}"}, na_rep="n/a"),
            use_container_width=True, height=500)

        st.caption("**ROOM_TO_RUN** = stock channel below its sector · "
                   "**LAGGING** = stock state weaker than its up sector · **BOTH** = both")
    else:
        st.info("No qualifying constituents today.")

with tab_manage:
    st.title("⚙️ Manage")
    st.caption("Adjust the scoring universe and keep an investor diary of the actions "
               "you actually took. Changes are saved on the server.")

    # ---------------- Scoring universe ----------------
    st.subheader("Scoring universe")
    _uni = manage_universe.universe.load_universe()
    _names = sorted(_uni.keys())
    st.caption(f"{len(_names)} tickers tracked. Adding a name maps it to your secular "
               "theme(s) and immediately backfills everything — 6 years of price, "
               "signals, fundamentals & moat (~2-3 min in the background). A removal "
               "takes effect immediately.")

    # Theme options for the selector — id → "Name (conviction)" label, regime excluded.
    _theme_opts = themes_io.theme_options()
    _theme_label = {tid: f"{name}  ·  {conv} conviction"
                    for tid, name, conv in _theme_opts}
    _theme_ids = [tid for tid, _, _ in _theme_opts]

    _ca, _cr = st.columns(2)
    with _ca:
        st.markdown("**➕ Add a company**")
        with st.form("add_ticker", clear_on_submit=True):
            _t = st.text_input("Ticker", placeholder="e.g. GEV")
            _sec = st.multiselect("Sector ETF(s)", SECTOR_ETFS,
                                  help="Buckets it for sector rotation (e.g. XLI).")
            _broad = st.radio("Benchmark", ["SPY", "QQQ"], horizontal=True)
            _themes = st.multiselect(
                "Secular theme(s)", _theme_ids,
                format_func=lambda tid: _theme_label.get(tid, tid),
                help="Maps the name into your thesis layer (Themes tab + narrative). "
                     "Leave empty for an off-thesis name.")
            if st.form_submit_button("Add to universe"):
                _tt = (_t or "").strip().upper()
                if not _tt:
                    st.warning("Enter a ticker.")
                elif _tt in _uni:
                    st.info(f"{_tt} is already in the universe.")
                else:
                    manage_universe.cmd_add(_tt, ",".join(_sec), _broad)
                    _ch = themes_io.add_ticker_to_themes(_tt, _themes)
                    _tmsg = (f"  Mapped to {len(_ch)} theme(s)." if _ch
                             else "  No theme assigned (off-thesis).")
                    # Fire the full backfill NOW (detached) — price, signals,
                    # fundamentals, moat, conviction — so there are no gaps. The
                    # lock in onboard.py coalesces rapid successive adds.
                    import subprocess, sys as _sys
                    _busy = onboard.is_running()
                    subprocess.Popen([_sys.executable, "onboard.py"],
                                     stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL,
                                     start_new_session=True)
                    st.cache_data.clear()
                    _bmsg = ("  A backfill is already running — it'll pick up "
                             f"{_tt} too." if _busy else
                             "  🔄 Full backfill started (price, signals, "
                             "fundamentals, moat) — ~2-3 min; refresh shortly.")
                    st.success(f"Added {_tt}.{_tmsg}{_bmsg}")
    with _cr:
        st.markdown("**➖ Remove a company**")
        with st.form("remove_ticker", clear_on_submit=True):
            _rt = st.selectbox("Ticker", ["— pick one —"] + _names)
            if st.form_submit_button("Remove from universe"):
                if _rt.startswith("—"):
                    st.warning("Pick a ticker to remove.")
                else:
                    manage_universe.cmd_remove(_rt)
                    _tch = themes_io.remove_ticker_from_themes(_rt)
                    _held = _rt in load_holdings()
                    st.cache_data.clear()
                    st.success(f"Removed {_rt} and purged its data."
                               + (f"  Unmapped from {len(_tch)} theme(s)." if _tch else "")
                               + (f"  ⚠️ Still in holdings.yaml — edit it if you sold."
                                  if _held else ""))
    st.divider()

    # ---------------- Investor diary ----------------
    st.subheader("📒 Investor diary")
    st.caption("Log what you actually did — the action history. Logging writes the "
               "**resulting weight** into holdings.yaml automatically (CASH offsets so "
               "the book stays at 100%), so the snapshot never goes stale. Trade % is "
               "the amount you transacted; New weight % is the size afterward.")
    try:
        _depl = cash_deployment.deployment()
        _recs = {f"{a['action']} {a['ticker']} (+{a['suggested_pct']}%)": a
                 for a in _depl.get("actions", []) + _depl.get("validations", [])}
    except Exception:
        _recs = {}

    _pick = st.selectbox("Pre-fill from a recommendation (optional)",
                         ["— Manual entry —"] + list(_recs.keys()), key="diary_pick")
    _pa = _recs.get(_pick)
    # Prefill: a TRIM/REVIEW transacts a negative amount; everything else positive.
    _is_trim = bool(_pa) and _pa.get("type") in ("TRIM", "REVIEW")
    _pre_trade = (f"{'-' if _is_trim else '+'}{_pa['suggested_pct']:g}") if _pa else ""
    _pre_new   = (f"{_pa['new_weight']:g}") if _pa and _pa.get("new_weight") is not None else ""
    with st.form("diary_log", clear_on_submit=True):
        _dc1, _dc2 = st.columns(2)
        _dt = _dc1.text_input("Ticker", value=(_pa["ticker"] if _pa else ""))
        _dact = _dc2.selectbox(
            "Action", diary.ACTIONS,
            index=(diary.ACTIONS.index("TRIM") if _is_trim else
                   diary.ACTIONS.index("ADD") if _pa and "ADD" in _pa["action"] else 0))
        _dc3, _dc4 = st.columns(2)
        _dtrade = _dc3.text_input("Trade % (signed)", value=_pre_trade,
                                  placeholder="e.g. +6 or -5")
        _dnew = _dc4.text_input("New weight % (resulting size)", value=_pre_new,
                                placeholder="e.g. 12", help="Written to holdings.yaml")
        _drec = st.text_input("Recommendation",
                              value=(f"{_pa['action']}: {_pa['detail']}" if _pa else ""))
        _dnote = st.text_input("Note (optional)")
        if st.form_submit_button("📝 Log it"):
            if not (_dt or "").strip():
                st.warning("Enter a ticker.")
            else:
                st.success(_log_and_apply(_dt, _dact, _dtrade, _dnew, _drec, _dnote))

    _dd = diary.load_diary()
    if len(_dd):
        st.dataframe(_dd.iloc[::-1], use_container_width=True, height=300, hide_index=True)
        st.download_button("⬇️ Download diary CSV", _dd.to_csv(index=False),
                           file_name="investor_diary.csv", mime="text/csv")
    else:
        st.info("No entries yet. Log an action above, or use the ✅ Log buttons on the Briefing tab.")
