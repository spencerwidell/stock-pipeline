import os
import requests
from datetime import datetime, timezone

# Load API key from .env file
def load_env():
    with open(".env") as f:
        for line in f:
            key, value = line.strip().split("=", 1)
            os.environ[key] = value

load_env()
API_KEY = os.environ["POLYGON_API_KEY"]

# Fetch the most recent daily close for a ticker
ticker = "AAPL"
url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/prev"
params = {"apiKey": API_KEY}

response = requests.get(url, params=params)
data = response.json()

print(f"Status: {response.status_code}")
print(f"Ticker: {ticker}")

if data.get("resultsCount", 0) > 0:
    result = data["results"][0]
    ts = datetime.fromtimestamp(result['t'] / 1000, tz=timezone.utc)
    print(f"Date:   {ts.strftime('%Y-%m-%d')}")
    print(f"Open:   {result['o']}")
    print(f"Close:  {result['c']}")
    print(f"High:   {result['h']}")
    print(f"Low:    {result['l']}")
    print(f"Volume: {result['v']}")
else:
    print("No results returned — check your API key and ticker")
