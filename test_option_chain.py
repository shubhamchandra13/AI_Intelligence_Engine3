from core.upstox_client import UpstoxClient
from config import SETTINGS

client = UpstoxClient()

NIFTY_KEY = "NSE_INDEX|Nifty 50"

print("Testing Option Chain Fetch (Auto Expiry)...")
chain = client.fetch_option_chain(NIFTY_KEY)

if chain:
    print("Option Chain Success! Items:", len(chain))
    print("Last Selected Expiry:", client.last_selected_expiry)
else:
    print("Option Chain Fetch Failed or Hanging.")
