from config import SETTINGS

def verify_aggressive_mode():
    print("🚀 CHECKING AGGRESSIVE TRAINING CONFIGURATION...")
    print("="*50)
    
    # Check 1: Confidence & Probability
    conf = SETTINGS["MIN_CONFIDENCE"]
    prob = SETTINGS["MIN_ML_WIN_PROBABILITY"]
    print(f"✅ Min Confidence:       {conf}%  (Aggressive if <= 45)")
    print(f"✅ Min Win Probability:  {prob}%  (Aggressive if <= 51)")
    
    # Check 2: Speed
    scan_interval = SETTINGS["STRUCTURE_SCAN_INTERVAL"]
    print(f"✅ Scan Interval:        {scan_interval}s   (Aggressive if <= 2)")
    
    # Check 3: Symbols
    symbols = SETTINGS["SYMBOLS"]
    print(f"✅ Active Indices:       {symbols}")
    
    # Check 4: Safety Filters
    sentiment = SETTINGS["STRICT_SENTIMENT_ALIGNMENT"]
    meta = SETTINGS["REQUIRE_META_TAKE_RECOMMENDATION"]
    print(f"✅ Sentiment Blocker:    {'⛔ ACTIVE' if sentiment else '🔓 DISABLED (Aggressive)'}")
    print(f"✅ Meta-Model Blocker:   {'⛔ ACTIVE' if meta else '🔓 DISABLED (Aggressive)'}")
    
    print("="*50)
    
    if conf <= 45 and prob <= 55 and not sentiment and len(symbols) >= 4:
        print("🔥 SYSTEM IS IN FULL BEAST MODE! (Maximum Learning Rate Enabled)")
    else:
        print("⚠️ System is still in Conservative Mode. Check config.py.")

if __name__ == "__main__":
    verify_aggressive_mode()
