from core.upstox_client import UpstoxClient
from core.data_fetcher import DataFetcher

client = UpstoxClient()
fetcher = DataFetcher()

BANKNIFTY_KEY = "NSE_INDEX|Nifty Bank"
NIFTY_KEY = "NSE_INDEX|Nifty 50"

print("Testing Spot Fetch...")

bank_spot = client.fetch_spot(BANKNIFTY_KEY)
nifty_spot = client.fetch_spot(NIFTY_KEY)

print("BANKNIFTY Spot:", bank_spot)
print("NIFTY Spot:", nifty_spot)

print("\nTesting Candle Fetch...")

candles = fetcher.get_candles("NIFTY", interval="1minute", limit=5)

if candles is not None and len(candles) > 0:
    print("Candle Sample:", candles.iloc[-1].to_dict())
else:
    print("Candle fetch failed")
