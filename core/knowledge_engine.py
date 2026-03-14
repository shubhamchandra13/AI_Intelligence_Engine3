# ============================================================
# 📚 SCHOLARLY AI KNOWLEDGE ENGINE
# Level 10: RAG-based Trading Wisdom Extraction
# ============================================================

import os
import fitz  # PyMuPDF
import json
import google.generativeai as genai
from dotenv import load_dotenv

class KnowledgeEngine:
    def __init__(self, book_dir=r"C:\Users\Shubham Chandra\Desktop\Stock Market Book"):
        load_dotenv()
        self.book_dir = book_dir
        self.wisdom_path = "database/trading_wisdom.json"
        # Force stable Gemini configuration
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def get_fallback_wisdom(self, filename):
        """Manual wisdom based on the specific books you provided."""
        fallbacks = {
            "epdf.pub_trading-for-a-living.pdf": [
                "Discipline is the key: The goal of a successful trader is to make the best trades, not the most money.",
                "Use the Triple Screen system: Never trade in the direction of the daily trend without checking the weekly trend first.",
                "Avoid trading when the market is in a choppy, sideways range (Range-Bound Protection)."
            ],
            "NSE Stock Market Book.pdf": [
                "In the Indian market, always follow the flow of Institutional Investors (FII/DII logic).",
                "Wait for the opening range breakout (ORB) before committing to a major trend direction.",
                "Volume confirmation is mandatory: A price move without volume is a trap."
            ],
            "options-trading-strategies-complete-guide-danes-scott-j-.pdf": [
                "Theta is your enemy as an option buyer: Avoid buying options with less than 5 days to expiry (unless scalping).",
                "Always look for high Implied Volatility (IV) expansion setups for quick option price jumps.",
                "Risk/Reward alignment: Only enter if the potential profit is at least 2x the stop loss."
            ],
            "Technical-Analysis.pdf": [
                "Break of Structure (BOS) confirms the true trend change; wait for the first pullback.",
                "Support and Resistance levels are 'Zones,' not precise numbers; wait for a sweep and rejection.",
                "Use Candlestick patterns (like Pin Bars/Engulfing) only at key institutional supply/demand zones."
            ]
        }
        return fallbacks.get(filename, ["Follow the trend.", "Manage your risk.", "Wait for a setup."])

    def extract_text_from_pdf(self, pdf_path, max_pages=15):
        """Extracts text from key pages of the PDF."""
        text = ""
        try:
            doc = fitz.open(pdf_path)
            # We take first 10 pages (intro/contents) and some middle pages
            total = len(doc)
            pages_to_read = list(range(min(10, total)))
            if total > 50:
                pages_to_read.extend([total//4, total//2, 3*total//4])
            
            for p_no in pages_to_read:
                if p_no < total:
                    text += doc[p_no].get_text()
            doc.close()
        except Exception as e:
            print(f"Error reading {pdf_path}: {e}")
        return text

    def build_wisdom_base(self):
        """Processes all books and builds a structured wisdom JSON."""
        print("🧠 Building AI Knowledge Base from Trading Books...")
        wisdom = {}
        
        if not os.path.exists(self.book_dir):
            print(f"❌ Book directory not found: {self.book_dir}")
            return False

        for file in os.listdir(self.book_dir):
            if file.endswith(".pdf"):
                print(f"📖 Analyzing: {file}...")
                path = os.path.join(self.book_dir, file)
                raw_text = self.extract_text_from_pdf(path)
                
                # Use Gemini to summarize into actionable rules
                prompt = f"""
                You are an expert institutional trader. I am giving you text from a trading book: '{file}'.
                Extract the top 5 'Golden Rules' or 'Institutional Principles' for Option Buying/Trading from this text.
                Format the output as a JSON list of strings.
                ONLY return the JSON list.
                """
                try:
                    # Attempt to use API
                    response = self.model.generate_content(prompt + "\n\n" + raw_text[:15000])
                    cleaned = response.text.replace("```json", "").replace("```", "").strip()
                    rules = json.loads(cleaned)
                    wisdom[file] = rules
                    import time
                    time.sleep(5)
                except Exception as e:
                    print(f"⚠️ API Error for {file}, using Fallback Knowledge: {e}")
                    wisdom[file] = self.get_fallback_wisdom(file)

        # Save to database
        os.makedirs("database", exist_ok=True)
        with open(self.wisdom_path, "w") as f:
            json.dump(wisdom, f, indent=4)
        
        print(f"✅ AI Knowledge Base updated at {self.wisdom_path}")
        return True

    def get_relevant_wisdom(self, symbol, bias):
        """Retrieves a random piece of wisdom for the current bias."""
        import random
        try:
            if not os.path.exists(self.wisdom_path): return "Stay disciplined."
            with open(self.wisdom_path, "r") as f:
                data = json.load(f)
            
            all_rules = []
            for book, rules in data.items():
                all_rules.extend(rules)
            
            if not all_rules: return "Risk management is key."
            return random.choice(all_rules)
        except:
            return "Follow the trend."

if __name__ == "__main__":
    ke = KnowledgeEngine()
    ke.build_wisdom_base()
