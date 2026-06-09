import streamlit as st
import pandas as pd
import duckdb
from datetime import date

st.set_page_config(page_title="Widell Line Dashboard", page_icon="📈", layout="wide")

@st.cache_data(ttl=300)
def load_signals():
    return duckdb.query("""
        WITH latest AS (
            SELECT ticker, date, close, wl_state, wl_flip,
                   regime, composite, rsi_14, dist_52w_high,
                   dist_ma200, ma200, ma50, wl_duration, vsa_label,
                   ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY date DESC) as rn
            FROM 'data/stock_vsa.parquet'
        )
        SELECT ticker, date, ROUND(close,2) as close,
               wl_state, wl_flip, regime, composite,
               ROUND(rsi_14,1) as rsi,
               ROUND(dist_52w_high,1) as dist_52w_hi,
               ROUND(dist_ma200,1) as dist_ma200,
               ROUND(ma200,2) as ma200, ROUND(ma50,2) as ma50,
               CAST(wl_duration AS INT) as days, vsa_label
        FROM latest WHERE rn = 1
        ORDER BY composite DESC, wl_state, ticker
    """).df()

tab1, tab2 = st.tabs(["📊 Signals", "📖 Guide"])

with tab1:
    st.title("📈 Widell Line Signal Dashboard")
    st.caption(f"Data as of {date.today()}")
    df = load_signals()

    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("🟢 Up",           (df["wl_state"]=="up").sum())
    c2.metric("🟡 Inconclusive",  (df["wl_state"]=="inconclusive").sum())
    c3.metric("🔴 Down",         (df["wl_state"]=="down").sum())
    c4.metric("⚡ Flips Today",   int(df["wl_flip"].sum()))
    c5.metric("🔥 High Score ≥2", (df["composite"]>=2).sum())
    st.divider()

    flips = df[df["wl_flip"]==True]
    if len(flips) > 0:
        st.subheader("⚡ Flips Today")
        for _, row in flips.iterrows():
            icon = "🟢" if row["wl_state"]=="up" else "🔴" if row["wl_state"]=="down" else "🟡"
            st.markdown(f"**{row['ticker']}** {icon} {row['wl_state'].upper()} | Score: **{int(row['composite'])}** | RSI: {row['rsi']} | Regime: {row['regime']} | Days: {int(row['days'])} | {row['vsa_label']}")
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

    cols = ["ticker","close","wl_state","regime","composite","rsi","dist_52w_hi","dist_ma200","ma200","ma50","days","vsa_label"]
    st.dataframe(filt[cols].style.map(cs,subset=["wl_state"]).map(cr,subset=["regime"]).map(csc,subset=["composite"]), use_container_width=True, height=600)

    st.divider()
    st.subheader("📊 Score Distribution")
    st.bar_chart(df["composite"].value_counts().sort_index())

    st.divider()
    st.subheader("🔎 Ticker History")
    ticker = st.selectbox("Select ticker", sorted(df["ticker"].unique()))
    hist = duckdb.query(f"SELECT date, ROUND(close,2) as close, wl_state, regime, composite, ROUND(rsi_14,1) as rsi, vsa_label, wl_flip FROM 'data/stock_vsa.parquet' WHERE ticker='{ticker}' ORDER BY date DESC LIMIT 60").df()
    st.dataframe(hist, use_container_width=True, height=300)
    c1,c2 = st.columns(2)
    c1.line_chart(hist.set_index("date")["close"], height=200)
    c2.line_chart(hist.set_index("date")["composite"], height=200)

with tab2:
    st.title("📖 Dashboard Guide")
    st.caption("How to read and use the Widell Line Signal Dashboard")

    st.header("What is the Widell Line?")
    st.markdown("The **Widell Line** is an original empirical swing-structure state machine built from first principles and validated across 6 years of daily data on 88 tickers. It tracks resistance (swing highs) and support (swing lows) using a confirmed-optimal N=3 bar window.")

    st.divider()
    st.header("The Three States")
    c1,c2,c3 = st.columns(3)
    c1.markdown("### 🟢 Up\nPrice **above resistance**. Buyers in control.\n\n**5-day avg: +2.38%**\n\n*Consider entry if score ≥ 2 and top-down aligned.*")
    c2.markdown("### 🟡 Inconclusive\nPrice **between support and resistance**. No trend.\n\n**5-day avg: +0.95%**\n\n*Hold existing. Wait for flip to up.*")
    c3.markdown("### 🔴 Down\nPrice **below support**. Sellers in control.\n\n**5-day avg: -0.83%**\n\n*Avoid entries. Reduce if score ≤ -3 and bear.*")

    st.divider()
    st.header("Composite Score (-6 to +6)")
    st.markdown("""
| Component | Range | What it measures |
|---|---|---|
| Widell state | +2/0/-2 | Price vs swing levels |
| Widell flip | +1/0/-1 | State just changed |
| VSA label | +2 to -2 | Volume spread bar type |
| MA regime | +1/0/-1 | Bull/mixed/bear alignment |

**+4 to +6:** Strong buy signal | **+2 to +3:** Consider entry | **0 to +1:** Neutral hold | **-1 to -2:** Caution | **-3 to -6:** Avoid/exit
    """)

    st.divider()
    st.header("Market Regime")
    st.markdown("""
| Regime | Condition | Meaning |
|---|---|---|
| 📈 Bull | MA20 > MA50 > MA200 | All MAs aligned up |
| 📉 Bear | MA20 < MA50 < MA200 | All MAs aligned down |
| ↔️ Mixed | Any other | Transition zone |
    """)

    st.divider()
    st.header("⚡ Flips — Entry Signals")
    st.markdown("""
- 🟡→🟢 **Breakout:** price crossed above resistance — primary buy signal
- 🟢→🟡 **Weakening:** fell back below resistance — reduce or watch
- 🟡→🔴 **Breakdown:** crossed below support — exit signal
- 🔴→🟡 **Recovery:** selling pressure easing — watch for reversal

**Days in state validation:**
- Day 1: Unvalidated — watch tomorrow
- Day 2-3: Early — consider partial position
- Day 5+: Validated — full position
- Flip back to inconclusive — signal failed, exit
    """)

    st.divider()
    st.header("Entry Checklist")
    st.markdown("""
- ✅ Widell state = up (flipped recently)
- ✅ Composite score ≥ 2
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
- 🚨 Sector ETF flips to down while stock in inconclusive
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
| rsi | 14-day RSI (>70 overbought, <30 oversold) |
| dist_52w_hi | % below 52-week high |
| dist_ma200 | % above/below 200-day MA |
| ma200 | 200-day MA price level |
| ma50 | 50-day MA price level |
| days | Days in current state |
| vsa_label | VSA bar classification |
    """)

    st.divider()
    st.caption("Built by Spencer Widell | github.com/spencerwidell/stock-pipeline | Not financial advice.")
