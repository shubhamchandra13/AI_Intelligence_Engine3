import logging
import os
import requests
import time
from bs4 import BeautifulSoup
import re
from datetime import datetime

# --- FORCE SILENCE ---
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
logging.getLogger("transformers").setLevel(logging.ERROR)

class SentimentEngine:
    def __init__(self):
        self.tokenizer = None
        self.model = None
        self.torch = None
        self.ready = False

        self.feeds = [
            "https://www.moneycontrol.com/rss/latestnews.xml", # India's #1 Financial site
            "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms", # Economic Times - Markets
            "https://economictimes.indiatimes.com/news/economy/rssfeeds/1373380680.cms", # Economic Times - Economy
            "https://www.livemint.com/rss/markets", # Livemint Markets
            "https://www.investing.com/rss/news_25.rss", # General Global/India News
            "https://search.cnbc.com/rs/search/view.xml?partnerId=2000&keywords=stock%20market" # Global Context
        ]

    def _ensure_ready(self):
        if self.ready:
            return True
        
        try:
            # Move imports inside to prevent early library noise
            import torch
            from transformers import AutoTokenizer, AutoModelForSequenceClassification
            
            # Suppress internal library logging
            logging.getLogger("transformers").setLevel(logging.ERROR)
            logging.getLogger("huggingface_hub").setLevel(logging.ERROR)

            # Load FinBERT - The industry standard for financial sentiment
            self.tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert", local_files_only=False)
            self.model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert", local_files_only=False)
            self.model.eval() # Set to evaluation mode
            self.torch = torch
            self.ready = True
            return True
        except Exception as e:
            # Log error if possible but don't crash
            self.ready = False
            return False

    def fetch_headlines_with_time(self, limit=10):
        """
        Level 8: Fetches headlines along with publication time with robust headers to bypass blocks.
        """
        import email.utils
        results = []
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }
        for url in self.feeds:
            try:
                resp = requests.get(url, timeout=10, headers=headers)
                if resp.status_code == 200:
                    # Robust parsing for both XML and RSS structures
                    soup = BeautifulSoup(resp.content, features="xml")
                    items = soup.find_all("item")
                    if not items:
                        # Fallback for some Atom/RSS feeds that use 'entry'
                        items = soup.find_all("entry")
                    
                    for item in items[:limit]:
                        title_tag = item.find("title")
                        pub_date_tag = item.find("pubDate") or item.find("published")
                        
                        if title_tag:
                            title = title_tag.text.strip()
                            ts = time.time()
                            if pub_date_tag:
                                try:
                                    dt = email.utils.parsedate_to_datetime(pub_date_tag.text)
                                    ts = dt.timestamp()
                                except: pass
                            
                            results.append({"text": title, "timestamp": ts})
            except Exception as e:
                # Silently fail for individual feeds to maintain loop speed
                continue
        
        # Sort by latest first
        results.sort(key=lambda x: x['timestamp'], reverse=True)
        return results

    def analyze_sentiment(self):
        if not self._ensure_ready(): return 0.0
            
        news_items = self.fetch_headlines_with_time()
        if not news_items: return 0.0
            
        try:
            headlines = [i["text"] for i in news_items]
            inputs = self.tokenizer(headlines, padding=True, truncation=True, return_tensors="pt")
            with self.torch.no_grad():
                outputs = self.model(**inputs)
                predictions = self.torch.nn.functional.softmax(outputs.logits, dim=-1)
            
            # 0: Positive, 1: Negative, 2: Neutral
            scores = predictions[:, 0] - predictions[:, 1]
            
            # --- 🔥 SENTIMENT DECAY LOGIC ---
            weighted_sum = 0
            total_weight = 0
            now = time.time()
            
            for idx, item in enumerate(news_items):
                age_mins = (now - item["timestamp"]) / 60
                # Decay Formula: 1.0 at 0 mins, 0.5 at 120 mins (2 hours), near 0 at 6 hours
                decay = 1.0 / (1.0 + (age_mins / 120)**2) 
                
                score = scores[idx].item()
                weighted_sum += score * decay
                total_weight += decay
            
            final_score = weighted_sum / total_weight if total_weight > 0 else 0
            return round(final_score, 2)
        except:
            return 0.0

    def get_sentiment_label(self, score):
        if score > 0.15: return "BULLISH (Neural)"
        if score < -0.15: return "BEARISH (Neural)"
        return "NEUTRAL (Neural)"
