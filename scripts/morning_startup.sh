#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
DATA_DIR="data"

if [[ ! -d "$DATA_DIR" ]]; then
    echo "ERROR: data directory missing at $DATA_DIR" >&2
    exit 1
fi
echo "Data directory confirmed."

echo "Pulling latest from GitHub. . ."
git pull --rebase

echo "Disk check:"
df -h . | tail -n 1

echo "Ready. Run: conda activate stock && ./scripts/run_checks.sh"

