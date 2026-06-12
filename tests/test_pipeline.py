import pytest
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# -----------------------------------------------------------------------
# Fixtures — load data once for all tests
# -----------------------------------------------------------------------

@pytest.fixture(scope="module")
def ohlcv():
    return pd.read_parquet("data/stock_ohlcv.parquet")

@pytest.fixture(scope="module")
def vsa():
    return pd.read_parquet("data/stock_vsa.parquet")

# -----------------------------------------------------------------------
# Data integrity tests
# -----------------------------------------------------------------------

def test_ohlcv_row_count(ohlcv):
    """Dataset should have a meaningful number of rows."""
    assert len(ohlcv) > 10000, f"Expected >10000 rows, got {len(ohlcv)}"

def test_ohlcv_required_columns(ohlcv):
    """Raw OHLCV must have all required columns."""
    required = ["ticker", "date", "open", "high", "low", "close", "volume"]
    for col in required:
        assert col in ohlcv.columns, f"Missing column: {col}"

def test_ohlcv_no_nulls(ohlcv):
    """Core OHLCV columns should have no nulls."""
    for col in ["ticker", "date", "open", "high", "low", "close", "volume"]:
        nulls = ohlcv[col].isnull().sum()
        assert nulls == 0, f"{col} has {nulls} null values"

def test_ohlcv_price_sanity(ohlcv):
    """High must be >= Low for every bar."""
    assert (ohlcv["high"] >= ohlcv["low"]).all(), "Found bars where high < low"

def test_ohlcv_positive_prices(ohlcv):
    """All prices must be positive."""
    for col in ["open", "high", "low", "close"]:
        assert (ohlcv[col] > 0).all(), f"{col} has non-positive values"

def test_ohlcv_positive_volume(ohlcv):
    """Volume must be positive."""
    assert (ohlcv["volume"] > 0).all(), "Volume has non-positive values"

def test_expected_tickers(ohlcv):
    """Key tickers must be present."""
    expected = ["AMZN", "NVDA", "MSFT", "SPY", "QQQ", "JPM"]
    for ticker in expected:
        assert ticker in ohlcv["ticker"].values, f"Missing ticker: {ticker}"

# -----------------------------------------------------------------------
# VSA feature tests
# -----------------------------------------------------------------------

def test_vsa_required_columns(vsa):
    """VSA Parquet must have all feature columns."""
    required = [
        "ticker", "date", "direction", "spread", "rel_spread",
        "rel_volume", "close_pos", "rsi_14", "macd", "macd_signal",
        "dist_52w_high", "dist_52w_low", "regime", "wl_state",
        "vsa_label", "composite",
    ]
    for col in required:
        assert col in vsa.columns, f"Missing column: {col}"

def test_direction_values(vsa):
    """Direction must be 'up' or 'down' only."""
    valid = {"up", "down"}
    actual = set(vsa["direction"].unique())
    assert actual <= valid, f"Unexpected direction values: {actual - valid}"

def test_close_pos_range(vsa):
    """Close position must be between 0 and 1."""
    valid = vsa["close_pos"].dropna()
    assert (valid >= 0).all() and (valid <= 1).all(), \
        "close_pos out of [0, 1] range"

def test_rsi_range(vsa):
    """RSI must be between 0 and 100."""
    valid = vsa["rsi_14"].dropna()
    assert (valid >= 0).all() and (valid <= 100).all(), \
        "RSI out of [0, 100] range"

def test_rel_volume_positive(vsa):
    """Relative volume must be positive (allowing rare zero-volume edge cases)."""
    valid = vsa["rel_volume"].dropna()
    zero_count = (valid <= 0).sum()
    assert zero_count <= 5, f"Too many non-positive rel_volume values: {zero_count}"

def test_regime_values(vsa):
    """Regime must be bull, bear, or mixed."""
    valid = {"bull", "bear", "mixed"}
    actual = set(vsa["regime"].unique())
    assert actual <= valid, f"Unexpected regime values: {actual - valid}"

def test_wl_state_values(vsa):
    """Widell Line state must be up, down, or inconclusive."""
    valid = {"up", "down", "inconclusive"}
    actual = set(vsa["wl_state"].unique())
    assert actual <= valid, f"Unexpected wl_state values: {actual - valid}"

def test_vsa_label_values(vsa):
    """VSA labels must be one of the expected types."""
    valid = {
        "buying_climax", "selling_climax", "effort_up", "effort_down",
        "no_demand", "no_supply", "neutral"
    }
    actual = set(vsa["vsa_label"].unique())
    assert actual <= valid, f"Unexpected vsa_label values: {actual - valid}"

def test_composite_score_range(vsa):
    """Composite score must be between -6 and 6."""
    assert vsa["composite"].min() >= -6, "composite below -6"
    assert vsa["composite"].max() <= 6, "composite above 6"

# -----------------------------------------------------------------------
# Widell Line logic tests
# -----------------------------------------------------------------------

def test_widell_state_separation(vsa):
    """Up state must have higher avg return than down state."""
    vsa_copy = vsa.copy()
    vsa_copy["return_5d"] = vsa_copy.groupby("ticker")["close"].transform(
        lambda x: (x.shift(-5) / x - 1) * 100)

    up_return   = vsa_copy[vsa_copy["wl_state"] == "up"]["return_5d"].mean()
    down_return = vsa_copy[vsa_copy["wl_state"] == "down"]["return_5d"].mean()

    assert up_return > down_return, \
        f"Up state ({up_return:.3f}) not > down state ({down_return:.3f})"

def test_widell_three_states_present(vsa):
    """All three Widell states must be present in the data."""
    states = set(vsa["wl_state"].unique())
    assert "up" in states, "Missing 'up' state"
    assert "down" in states, "Missing 'down' state"
    assert "inconclusive" in states, "Missing 'inconclusive' state"

# -----------------------------------------------------------------------
# Pipeline consistency tests
# -----------------------------------------------------------------------

def test_row_count_preserved(ohlcv, vsa):
    """VSA row count must equal OHLCV minus the low-volume junk bars that
    vsa_features.py drops (volume > 1000 filter)."""
    expected = int((ohlcv["volume"] > 1000).sum())
    assert len(vsa) == expected, \
        f"Row count mismatch: vsa={len(vsa)}, expected (volume>1000)={expected}, " \
        f"ohlcv total={len(ohlcv)}"

def test_ticker_preserved(ohlcv, vsa):
    """All tickers in OHLCV must appear in VSA."""
    ohlcv_tickers = set(ohlcv["ticker"].unique())
    vsa_tickers   = set(vsa["ticker"].unique())
    assert ohlcv_tickers == vsa_tickers, \
        f"Ticker mismatch: {ohlcv_tickers - vsa_tickers}"


# -----------------------------------------------------------------------
# holdings_io.apply_trade — logging a trade keeps the snapshot in sync (Session 45)
# -----------------------------------------------------------------------

_SAMPLE_HOLDINGS = """\
# A comment that must survive a write.
portfolio:
  total_value: 1000000
positions:
  NVDA: 11
  MSFT: 11
  AMZN: 11
  ELF:  10
  SOFI: 8
  PLTR: 7
  TSLA: 7
  META: 7
  AVGO: 7
  TSM:  5
  CASH: 16
overrides:
  TSLA: core
"""


@pytest.fixture
def holdings_file(tmp_path):
    p = tmp_path / "holdings.yaml"
    p.write_text(_SAMPLE_HOLDINGS)
    return str(p)


def _sum_book(path):
    import holdings_io
    pos = holdings_io.load_positions(path, include_cash=True)
    return round(sum(float(v) for v in pos.values()), 1)


def test_apply_trade_add_offsets_cash(holdings_file):
    import holdings_io
    res = holdings_io.apply_trade("AVGO", 15, holdings_file)
    assert (res["old"], res["new"]) == (7.0, 15.0)
    assert res["cash_old"] == 16.0 and res["cash_new"] == 8.0   # +8 add → cash -8
    assert _sum_book(holdings_file) == 100.0


def test_apply_trade_trim_returns_cash(holdings_file):
    import holdings_io
    res = holdings_io.apply_trade("ELF", 3, holdings_file)
    assert res["cash_new"] == 23.0                              # -7 trim → cash +7
    assert _sum_book(holdings_file) == 100.0


def test_apply_trade_inserts_new_holding(holdings_file):
    import holdings_io
    holdings_io.apply_trade("RTX", 3, holdings_file)
    pos = holdings_io.load_positions(holdings_file, include_cash=True)
    assert pos.get("RTX") == "3" and float(pos["CASH"]) == 13.0
    assert _sum_book(holdings_file) == 100.0


def test_apply_trade_full_exit_removes_line(holdings_file):
    import holdings_io
    holdings_io.apply_trade("ELF", 0, holdings_file)
    pos = holdings_io.load_positions(holdings_file, include_cash=True)
    assert "ELF" not in pos and float(pos["CASH"]) == 26.0
    assert _sum_book(holdings_file) == 100.0


def test_apply_trade_preserves_comments_and_overrides(holdings_file):
    import holdings_io
    holdings_io.apply_trade("AVGO", 15, holdings_file)
    text = open(holdings_file).read()
    assert "# A comment that must survive a write." in text
    assert holdings_io.load_overrides(holdings_file) == {"TSLA": "core"}


# -----------------------------------------------------------------------
# diary — two-field schema + legacy migration (Session 45)
# -----------------------------------------------------------------------

def test_diary_logs_trade_and_new_weight(tmp_path):
    import diary
    p = str(tmp_path / "d.csv")
    diary.log_action("GOOG", "BUY", trade_pct="+3", new_weight="3",
                     recommendation="NEW SETUP", path=p)
    df = diary.load_diary(p)
    row = df.iloc[0]
    assert row["trade_pct"] == "+3" and row["new_weight"] == "3"
    assert list(df.columns) == diary.FIELDS


def test_diary_migrates_legacy_schema(tmp_path):
    import csv, diary
    p = str(tmp_path / "legacy.csv")
    with open(p, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=diary._LEGACY_FIELDS)
        w.writeheader()
        w.writerow({"date": "2026-06-12", "ticker": "SOFI", "action": "TRIM",
                    "weight": "3%", "recommendation": "trim", "note": ""})
        w.writerow({"date": "2026-06-12", "ticker": "AVGO", "action": "ADD",
                    "weight": "8%", "recommendation": "add", "note": ""})
    # A new write triggers migration: ADD's weight was a delta, TRIM's a target.
    diary.log_action("GLW", "BUY", trade_pct="+3", new_weight="3", path=p)
    df = diary.load_diary(p)
    assert list(df.columns) == diary.FIELDS
    sofi = df[df.ticker == "SOFI"].iloc[0]
    avgo = df[df.ticker == "AVGO"].iloc[0]
    assert sofi["new_weight"] == "3%" and sofi["trade_pct"] == ""
    assert avgo["trade_pct"] == "8%" and avgo["new_weight"] == ""
