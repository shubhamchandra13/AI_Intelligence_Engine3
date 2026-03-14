import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("UPSTOX_API_KEY")
REDIRECT_URI = os.getenv("UPSTOX_REDIRECT_URI")

if not API_KEY or not REDIRECT_URI:
    print("Error: .env file mein API_KEY ya REDIRECT_URI missing hai!")
else:
    login_url = f"https://api.upstox.com/v2/login/authorization/dialog?response_type=code&client_id={API_KEY}&redirect_uri={REDIRECT_URI}"
    print("\n" + "="*60)
    print("🚀 UPSTOX LOGIN URL GENERATED")
    print("="*60)
    print(f"\n1. Niche diye gaye link ko browser mein kholiye:\n\n{login_url}")
    print("\n2. Login karne ke baad, aapka browser ek error page ya blank page dikhayega.")
    print("3. Us page ke URL (Address Bar) ko dekhiye, wahan '?code=XXXXXX' likha hoga.")
    print("4. Woh 'code' (XXXXXX) mujhe bataiye, main token update kar dunga.")
    print("="*60)
