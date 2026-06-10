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
                   dist_ma200, ma200, ma50, vsa_label, wl_duration,
                   flip_price, resistance,
                   ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY date DESC) as rn
            FROM 'data/stock_vsa.parquet'
        )
        SELECT ticker, date, ROUND(close,2) as close,
               wl_state, wl_flip, regime, composite,
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
               ROUND((close - flip_price) / flip_price * 100, 1) as gap_from_flip
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

    st.subheader("🟢 Up State — Entry & Pullback Analysis")
    up_df = df[df["wl_state"]=="up"].copy()
    if len(up_df) > 0:
        for _, row in up_df.iterrows():
            gap  = f"{row['gap_from_flip']:+.1f}%" if pd.notna(row["gap_from_flip"]) else "N/A"
            pb   = f"{row['level_type']}→${row['key_level']:.2f}" if pd.notna(row["key_level"]) else "N/A"
            days = int(row["days"]) if pd.notna(row["days"]) else 0
            chase = "🔴 CHASING" if pd.notna(row["gap_from_flip"]) and row["gap_from_flip"] > 5 else \
                    "🟡 ELEVATED" if pd.notna(row["gap_from_flip"]) and row["gap_from_flip"] > 2 else \
                    "🟢 AT ENTRY"
            st.markdown(
                f"**{row['ticker']}** ${row['close']:.2f} "
                f"| {chase} gap={gap} "
                f"| Pullback target: **{pb}** "
                f"| Days in up: {days} "
                f"| Score: {int(row['composite'])} "
                f"| Regime: {row['regime']}"
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

    cols = ["ticker","close","wl_state","regime","composite","rsi",
            "dist_52w_hi","dist_ma200","ma200","ma50","days",
            "gap_from_flip","key_level","level_type","vsa_label"]
    st.dataframe(
        filt[cols].style
            .map(cs,   subset=["wl_state"])
            .map(cr,   subset=["regime"])
            .map(csc,  subset=["composite"])
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
| rsi | 14-day RSI |
| dist_52w_hi | % below 52-week high |
| dist_ma200 | % above/below 200-day MA |
| ma200 | 200-day MA price |
| ma50 | 50-day MA price |
| days | Days in current state |
| gap_from_flip | % move since flip (green<2%, yellow 2-5%, red>5%) |
| key_level | Key price level: pullback target (up), breakout level (inconclusive), resistance (down) |
| vsa_label | VSA bar classification |
    """)

    st.divider()
    st.caption("Built by Spencer Widell | github.com/spencerwidell/stock-pipeline | Not financial advice.")
