from core.sentiment_engine import SentimentEngine

engine = SentimentEngine()
print("Checking News Feeds...")
headlines = engine.fetch_latest_headlines(limit=2)

if headlines:
    print(f"Total Headlines found: {len(headlines)}")
    for i, h in enumerate(headlines[:5]):
        print(f"{i+1}. {h}")
else:
    print("No headlines found. Check internet or source URLs.")
