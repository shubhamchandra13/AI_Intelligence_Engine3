
import os
import requests
from dotenv import load_dotenv

load_dotenv(override=True)

def test_iv():
    token = os.getenv("UPSTOX_ACCESS_TOKEN")
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    # BANKNIFTY instrument key
    instrument_key = "NSE_INDEX|Nifty Bank"
    
    # 1. Get Expiry
    url_expiry = f"https://api.upstox.com/v2/option/contract?instrument_key={instrument_key}"
    print(f"Fetching expiry from: {url_expiry}")
    resp = requests.get(url_expiry, headers=headers)
    print(f"Expiry Response Code: {resp.status_code}")
    if resp.status_code != 200:
        print(f"Error: {resp.text}")
        return

    data = resp.json()
    contracts = data.get("data", [])
    if not contracts:
        print("No contracts found")
        return
        
    expiries = sorted(list(set(item["expiry"] for item in contracts if "expiry" in item)))
    expiry_date = expiries[0]
    print(f"Selected Expiry: {expiry_date}")

    # 2. Get Option Chain
    url_chain = f"https://api.upstox.com/v2/option/chain?instrument_key={instrument_key}&expiry_date={expiry_date}"
    print(f"Fetching chain from: {url_chain}")
    resp = requests.get(url_chain, headers=headers)
    print(f"Chain Response Code: {resp.status_code}")
    if resp.status_code != 200:
        print(f"Error: {resp.text}")
        return

    data = resp.json()
    chain = data.get("data", [])
    print(f"Chain length: {len(chain)}")
    
    if chain:
        sample = chain[len(chain)//2]
        print(f"Sample Strike: {sample.get('strike_price')}")
        call = sample.get("call_options", {})
        print(f"Call IV: {call.get('market_data', {}).get('iv')}")
        print(f"Greeks: {call.get('option_greeks')}")

if __name__ == "__main__":
    test_iv()
