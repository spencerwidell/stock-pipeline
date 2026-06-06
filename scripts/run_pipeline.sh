#!/usr/bin/env bash
set -euo pipefail

source /home/datasci/miniconda3/etc/profile.d/conda.sh
conda activate stock
cd "$(dirname "$0")/.."

LOGDIR="logs"
mkdir -p "$LOGDIR"

LOGFILE="$LOGDIR/fetch_$(date +%Y%m%d_%H%M).log"

echo "Starting fetch pipeline..."
echo "Log: $LOGFILE"

nohup python fetch_stock.py > "$LOGFILE" 2>&1 &

echo "PID: $!"
echo "Follow with: tail -f $LOGFILE"
