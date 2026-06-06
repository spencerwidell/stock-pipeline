import duckdb

PARQUET = "data/stock_ohlcv.parquet"

def q(sql):
    print(duckdb.query(sql).df().to_string(index=False))
    print()

print("=== Top 5 closes ===")
q(f"SELECT ticker, date, close FROM '{PARQUET}' ORDER BY close DESC LIMIT 5")

print("=== Average close by ticker ===")
q(f"SELECT ticker, ROUND(AVG(close), 2) as avg_close FROM '{PARQUET}' GROUP BY ticker ORDER BY avg_close DESC")

print("=== Top 10 daily returns ===")
q(f"""
    SELECT ticker, date, ROUND((close - open) / open * 100, 2) as daily_return_pct
    FROM '{PARQUET}'
    ORDER BY daily_return_pct DESC
    LIMIT 10
""")
