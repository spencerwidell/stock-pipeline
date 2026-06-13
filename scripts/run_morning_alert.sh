#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

mkdir -p logs
LOG="logs/morning_$(date +%Y%m%d_%H%M).log"

echo "=== Morning Alert Run $(date) ===" | tee "$LOG"

# --- Activate the `stock` conda env, locating conda across machines ---
# Same portable pattern as run_daily.sh: works on the local box (/home/datasci)
# and AWS (/home/ubuntu) without hardcoding a path. Override with CONDA_SH=...
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

# Morning alert always sends — no SEND_TELEGRAM gate. Uses yesterday's parquet
# plus live Polygon snapshot prices; does not re-run the pipeline.
echo "Sending morning alert..." | tee -a "$LOG"
python morning_alert.py >> "$LOG" 2>&1

# Idea of the Day — the one thing that matters today (Destination Book + Tide).
# Decoupled + fail-soft so it can't block the morning alert; also records today's
# tide so tide-turn detection has a prior day to compare against.
echo "Sending Idea of the Day..." | tee -a "$LOG"
python -c "import idea_of_the_day as i; i.send_idea()" >> "$LOG" 2>&1 || true

echo "=== Done $(date) ===" | tee -a "$LOG"
