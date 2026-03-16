from core.data_fetcher import DataFetcher
from core.upstox_client import UpstoxClient

class DataProvider:
    """
    Abstracts data access for both LIVE and REPLAY modes.
    """
    def __init__(self, mode_manager, data_fetcher: DataFetcher, upstox_client: UpstoxClient, ws_engine=None):
        self.mode_manager = mode_manager
        self.data_fetcher = data_fetcher
        self.upstox_client = upstox_client
        self.ws_engine = ws_engine
        self.replay_data_source = None # Placeholder for Replay Engine

    def get_candles(self, symbol, interval="1minute", limit=2000):
        if self.mode_manager.is_live():
            return self.data_fetcher.get_candles(symbol, interval, limit)
        elif self.mode_manager.is_replay():
            # In Replay mode, this should come from the Replay Engine's current step
            if self.replay_data_source:
                 return self.replay_data_source.get_current_candles(symbol)
            else:
                return None
        return None

    def get_ltp(self, symbol):
        if self.mode_manager.is_live():
            if self.ws_engine:
                # Need to map symbol to instrument key if possible, or pass key directly
                # Assuming symbol is passed, we might need a lookup map or rely on caller passing key
                # For now, let's assume the caller handles key mapping if using ws_engine directly
                # But to abstract it properly:
                # We need the instrument key from settings or a map
                pass
            # Fallback to REST API if WS not available or for consistency
            return self.data_fetcher.get_spot(symbol)
        elif self.mode_manager.is_replay():
            if self.replay_data_source:
                return self.replay_data_source.get_current_ltp(symbol)
        return 0.0

    def get_market_snapshot(self, symbol, interval="1minute", limit=2000):
        """
        Returns a unified snapshot containing candles and current price.
        """
        candles = self.get_candles(symbol, interval, limit)
        ltp = self.get_ltp(symbol)
        return {
            "symbol": symbol,
            "candles": candles,
            "ltp": ltp,
            "timestamp": None # Should be filled with current simulation time or live time
        }
