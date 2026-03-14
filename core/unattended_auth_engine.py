# ============================================================
# 🔑 UNATTENDED AUTH ENGINE – BROWSER-LESS LOGIN
# Level 8: Zero-Touch Authentication using TOTP
# ============================================================

import os
import requests
import pyotp
import urllib.parse
from dotenv import load_dotenv, set_key

class UnattendedAuthEngine:
    def __init__(self):
        load_dotenv(override=True)
        self.api_key = os.getenv("UPSTOX_API_KEY")
        self.api_secret = os.getenv("UPSTOX_API_SECRET")
        self.redirect_uri = os.getenv("UPSTOX_REDIRECT_URI")
        self.mobile_no = os.getenv("UPSTOX_MOBILE_NO")
        self.pin = os.getenv("UPSTOX_PIN")
        self.totp_key = os.getenv("UPSTOX_TOTP_KEY")
        
        self.session = requests.Session()

    def login(self):
        """
        Executes the full automated login flow.
        """
        if not all([self.api_key, self.api_secret, self.redirect_uri, self.mobile_no, self.pin, self.totp_key]):
            return False, "Missing credentials in .env (PIN, TOTP_KEY, or MOBILE_NO)"

        try:
            # 1. Get Auth URL
            auth_url = f"https://api.upstox.com/v2/login/auth/v2/code?client_id={self.api_key}&redirect_uri={urllib.parse.quote(self.redirect_uri)}&response_type=code"
            
            # 2. Step 1: Send Mobile Number
            resp = self.session.post('https://api.upstox.com/v2/login/v2/oauth/authorize/mobile', 
                                    json={'mobile_no': self.mobile_no},
                                    headers={'Referer': auth_url})
            
            if resp.status_code != 200: return False, f"Mobile submission failed: {resp.text}"
            request_id = resp.json().get('data', {}).get('request_id')

            # 3. Step 2: Send TOTP
            totp = pyotp.TOTP(self.totp_key.replace(" ", "")).now()
            resp = self.session.post('https://api.upstox.com/v2/login/v2/oauth/authorize/otp',
                                    json={'request_id': request_id, 'otp': totp},
                                    headers={'Referer': auth_url})
            
            if resp.status_code != 200: return False, f"TOTP submission failed: {resp.text}"

            # 4. Step 3: Send PIN
            resp = self.session.post('https://api.upstox.com/v2/login/v2/oauth/authorize/pin',
                                    json={'request_id': request_id, 'pin': self.pin},
                                    headers={'Referer': auth_url})
            
            if resp.status_code != 200: return False, f"PIN submission failed: {resp.text}"

            # 5. Step 4: Finalize & Get Code
            # This redirect happens automatically in a browser, here we hit the URL to get the 'code'
            resp = self.session.get(auth_url, allow_redirects=False)
            
            # The code is in the Location header
            location = resp.headers.get('Location', '')
            if 'code=' not in location:
                return False, "Could not find authorization code in redirect"
            
            code = location.split('code=')[1].split('&')[0]

            # 6. Step 5: Exchange Code for Token
            token_url = "https://api.upstox.com/v2/login/authorization/token"
            data = {
                'code': code,
                'client_id': self.api_key,
                'client_secret': self.api_secret,
                'redirect_uri': self.redirect_uri,
                'grant_type': 'authorization_code'
            }
            
            token_resp = requests.post(token_url, data=data)
            token_data = token_resp.json()

            if 'access_token' in token_data:
                new_token = token_data['access_token']
                # Update .env file
                set_key(".env", "UPSTOX_ACCESS_TOKEN", new_token)
                return True, "Login Successful. Token Updated."
            else:
                return False, f"Token exchange failed: {token_data}"

        except Exception as e:
            return False, f"Auto-Login Exception: {e}"

if __name__ == "__main__":
    engine = UnattendedAuthEngine()
    success, msg = engine.login()
    print(f"Result: {success} | {msg}")
