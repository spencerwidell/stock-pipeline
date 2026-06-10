#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

LOG="logs/daily_$(date +%Y%m%d_%H%M).log"
mkdir -p logs

echo "=== Daily Pipeline Run $(date) ===" | tee "$LOG"

# --- Activate the `stock` conda env, locating conda across machines ---
# Portable: works on the local box (/home/datasci) and AWS (/home/ubuntu)
# without hardcoding a path. Override with CONDA_SH=/path/to/conda.sh if needed.
CONDA_SH="${CONDA_SH:-}"
if [ -z "$CONDA_SH" ]; then
    for c in "$HOME/miniconda3/etc/profile.d/conda.sh" \
             "$HOME/anaconda3/etc/profile.d/conda.sh" \
             "$HOME/miniforge3/etc/profile.d/conda.sh" \
             "/opt/conda/etc/profile.d/conda.sh"; do
        if [ -f "$c" ]; then CONDA_SH="$c"; break; fi
    done
fi
if [ -z "$CONDA_SH" ] || [ ! -f "$CONDA_SH" ]; then
    echo "ERROR: could not locate conda.sh (looked under \$HOME/{miniconda3,anaconda3,miniforge3}, /opt/conda)" | tee -a "$LOG"
    exit 1
fi
# shellcheck disable=SC1090
source "$CONDA_SH"
conda activate stock

echo "Fetching data..." | tee -a "$LOG"
python fetch_stock.py >> "$LOG" 2>&1

echo "Building features..." | tee -a "$LOG"
python vsa_features.py     >> "$LOG" 2>&1
python vsa_labels.py       >> "$LOG" 2>&1
python widell_line.py      >> "$LOG" 2>&1
python composite_score.py  >> "$LOG" 2>&1
python conviction_score.py >> "$LOG" 2>&1

# Tests are a safety check, not a gate — a regression should be logged loudly
# but must not suppress the daily signal/alert once the data pipeline succeeded.
echo "Running tests..." | tee -a "$LOG"
set +e
pytest tests/ -q --tb=short >> "$LOG" 2>&1
TEST_RC=$?
set -e
if [ "$TEST_RC" -ne 0 ]; then
    echo "WARNING: pytest failed (rc=$TEST_RC) — see $LOG" | tee -a "$LOG"
fi

# Earnings dates — self-throttling (only refetches when >= REFRESH_DAYS stale),
# so it's safe to call daily. Fail-soft: a yfinance hiccup must not stop signals.
echo "Refreshing earnings dates..." | tee -a "$LOG"
python fetch_earnings.py >> "$LOG" 2>&1 || true

echo "Generating signals..." | tee -a "$LOG"
python daily_signals.py | tee -a "$LOG"

# Optional Telegram push — enabled in the AWS cron via SEND_TELEGRAM=1.
# Left off for local/manual runs so testing doesn't ping the phone.
if [ "${SEND_TELEGRAM:-0}" = "1" ]; then
    echo "Sending Telegram alert..." | tee -a "$LOG"
    python telegram_alert.py >> "$LOG" 2>&1

    # Plain-English LLM briefing (interprets the signals above). Self-contained
    # and fail-soft — it logs and exits 0 on any error so a Claude API hiccup
    # never fails the pipeline. `|| true` is belt-and-suspenders for set -e.
    echo "Sending narrative alert..." | tee -a "$LOG"
    python narrative_alert.py >> "$LOG" 2>&1 || true
fi

echo "=== Done $(date) ===" | tee -a "$LOG"
