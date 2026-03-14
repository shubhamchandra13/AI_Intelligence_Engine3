import os
from dotenv import load_dotenv

load_dotenv()

def check_autonomy_readiness():
    print("🤖 CHECKING AUTONOMY READINESS...")
    
    # 1. Check Auth Credentials
    totp_key = os.getenv("UPSTOX_TOTP_KEY")
    mobile = os.getenv("UPSTOX_MOBILE_NO")
    pin = os.getenv("UPSTOX_PIN")
    
    if not totp_key or not mobile or not pin:
        print("❌ FULL AUTONOMY FAILED: Missing Auto-Login Credentials.")
        print(f"   - TOTP_KEY: {'✅ Found' if totp_key else '❌ MISSING (Required for Auto-Login)'}")
        print(f"   - MOBILE_NO: {'✅ Found' if mobile else '❌ MISSING'}")
        print(f"   - PIN: {'✅ Found' if pin else '❌ MISSING'}")
        print("   -> Without these, you must manually log in every morning.")
    else:
        print("✅ AUTH SUBSYSTEM: READY for Zero-Touch Login.")

    # 2. Check Execution Mode
    # We inspect main.py to see which engine is active
    try:
        with open("main.py", "r", encoding="utf-8") as f:
            content = f.read()
            if "InstitutionalPaperExecutionEngine" in content and "RealExecutionEngine" not in content:
                print("⚠️ EXECUTION SUBSYSTEM: SIMULATION MODE (Paper Trading).")
                print("   -> Real money will NOT be used.")
            else:
                print("⚠️ EXECUTION SUBSYSTEM: Unknown/Mixed Mode.")
    except:
        print("❌ Could not verify Execution Mode.")

if __name__ == "__main__":
    check_autonomy_readiness()
