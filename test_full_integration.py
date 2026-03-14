# ============================================================
# 🧪 FULL SYSTEM INTEGRATION TEST (Level 7 Verification)
# Audit Item #7: Boot -> Scan -> Sync -> Log Cycle Test
# ============================================================

import os
import sys
import json
import time
import pandas as pd
from datetime import datetime

# Import system modules
from config import SETTINGS
from core.health_check import HealthCheck
from core.data_guards import DataGuards
from core.data_fetcher import DataFetcher
from engines.trade_intelligence_engine import TradeIntelligenceEngine
from engines.confidence_engine import calculate_confidence
from core.runtime_control import write_runtime_state

def run_integration_test():
    print("\n" + "═"*60)
    print("🧪 STARTING FULL SYSTEM INTEGRATION AUDIT")
    print("═"*60)

    # 1. TEST: Health Diagnostics
    print("\n[STEP 1/5] Testing Startup Diagnostics...")
    hc = HealthCheck(SETTINGS)
    hc_result = hc.run_all()
    if not hc_result:
        print("⚠️ HealthCheck failed (Expected if offline/no token), continuing to logic test...")
    else:
        print("✅ Step 1 Passed: Diagnostics functional.")

    # 2. TEST: Data Integrity & Guards
    print("\n[STEP 2/5] Testing Data Guards & Validation...")
    # Simulate a fake stale dataframe
    stale_df = pd.DataFrame({"close": [100]*100}, index=pd.date_range("2020-01-01", periods=100, freq="1min"))
    is_valid, msg = DataGuards.validate_candles(stale_df, "TEST_SYM")
    if not is_valid and "STALE" in msg:
        print(f"✅ Step 2 Passed: DataGuard correctly caught stale data: {msg}")
    else:
        print(f"❌ Step 2 Failed: DataGuard missed stale data check.")

    # 3. TEST: Intelligence & Hive Mind
    print("\n[STEP 3/5] Testing Hive Mind & Analytics...")
    tie = TradeIntelligenceEngine()
    tie.refresh()
    stats = tie.get_basic_stats()
    if "total_trades" in stats:
        print(f"✅ Step 3 Passed: Intelligence Engine loaded data. Trades found: {stats['total_trades']}")
        if "hive_sync" in stats:
            print(f"   ℹ️ Hive Mind Status: {'Connected' if stats['hive_sync'] else 'Isolated'}")
    else:
        print("❌ Step 3 Failed: Intelligence Engine stats are empty.")

    # 4. TEST: State Synchronization (Audit Item #5)
    print("\n[STEP 4/5] Testing Single Source of Truth (State Sync)...")
    # Using a unique key that main.py won't overwrite immediately
    test_marker = f"TEST_{int(time.time())}"
    test_state = {
        "integration_test_marker": test_marker,
        "last_updated": {"test": datetime.now().isoformat()}
    }
    write_runtime_state(test_state)
    time.sleep(0.5)
    
    if os.path.exists("database/runtime_state.json"):
        with open("database/runtime_state.json", "r") as f:
            saved_state = json.load(f)
        
        # We check if our marker exists (even if main.py added other keys)
        if saved_state.get("integration_test_marker") == test_marker:
            print("✅ Step 4 Passed: Runtime State synchronized (Marker found).")
        else:
            print(f"❌ Step 4 Failed: Marker mismatch.")
            print(f"   Note: This can happen if background main.py is extremely fast.")
    else:
        print("❌ Step 4 Failed: runtime_state.json not found.")

    # 5. TEST: Audit Logging (Audit Item #9)
    print("\n[STEP 5/5] Testing Persistent Rejection Logging...")
    from engines.trade_logger import TradeLogger
    logger = TradeLogger()
    test_reason = "INTEGRATION_TEST_REJECTION_REASON"
    logger.log_rejection("TEST_INDEX", test_reason, 45.5)
    
    if os.path.exists("database/trade_rejections.log"):
        with open("database/trade_rejections.log", "r") as f:
            content = f.read()
        if test_reason in content:
            print("✅ Step 5 Passed: Rejection reason persistently logged.")
        else:
            print("❌ Step 5 Failed: Rejection reason missing from log.")
    else:
        print("❌ Step 5 Failed: trade_rejections.log not created.")

    print("\n" + "═"*60)
    print("🏁 INTEGRATION AUDIT COMPLETE")
    print("═"*60 + "\n")

if __name__ == "__main__":
    run_integration_test()
