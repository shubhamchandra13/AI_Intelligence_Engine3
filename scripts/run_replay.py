import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engines.historical_replay_engine import HistoricalReplayEngine
from engines.strategy_engine import StrategyEngine
from engines.institutional_paper_execution_engine import InstitutionalPaperExecutionEngine
from engines.trade_logger import TradeLogger
from core.data_fetcher import DataFetcher
from config import SETTINGS

def run_replay():
    print("Initializing Historical Replay...")
    
    strategy_engine = StrategyEngine()
    execution_engine = InstitutionalPaperExecutionEngine(initial_capital=SETTINGS["INITIAL_CAPITAL"], rl_engine=None)
    db_logger = TradeLogger()
    
    replay_engine = HistoricalReplayEngine(strategy_engine, execution_engine, db_logger)
    
    data_fetcher = DataFetcher()
    symbols = SETTINGS.get("REPLAY_SYMBOLS", ["BANKNIFTY", "NIFTY"])
    
    if replay_engine.load_data(data_fetcher, symbols, start_date=None, end_date=None, interval="1minute"):
        replay_engine.start_replay()
    else:
        print("Failed to load replay data.")

if __name__ == "__main__":
    run_replay()
