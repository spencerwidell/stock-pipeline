#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "Running pipeline tests..."
pytest tests/ -v --tb=short

echo ""
echo "Checking data freshness..."
python -c "
import pandas as pd
df = pd.read_parquet('data/stock_ohlcv.parquet')
latest = df['date'].max()
print(f'Latest data: {latest.date()}')
print(f'Tickers: {df[\"ticker\"].nunique()}')
print(f'Rows: {len(df):,}')
"
echo "All checks passed."
