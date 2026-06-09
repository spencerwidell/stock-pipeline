#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

LOG="logs/daily_$(date +%Y%m%d_%H%M).log"
mkdir -p logs

echo "=== Daily Pipeline Run $(date) ===" | tee "$LOG"

source /home/datasci/miniconda3/etc/profile.d/conda.sh
conda activate stock

echo "Fetching data..." | tee -a "$LOG"
python fetch_stock.py >> "$LOG" 2>&1

echo "Building features..." | tee -a "$LOG"
python vsa_features.py >> "$LOG" 2>&1
python vsa_labels.py >> "$LOG" 2>&1
python widell_line.py >> "$LOG" 2>&1
python composite_score.py >> "$LOG" 2>&1

echo "Running tests..." | tee -a "$LOG"
pytest tests/ -q --tb=short >> "$LOG" 2>&1

echo "Generating signals..." | tee -a "$LOG"
python daily_signals.py | tee -a "$LOG"

echo "=== Done $(date) ===" | tee -a "$LOG"
