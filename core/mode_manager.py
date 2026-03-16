from datetime import datetime, time
import pytz
from config import SETTINGS

class ModeManager:
    """
    Manages the operating mode of the AI Engine.
    Modes:
    - LIVE_PAPER: Real-time trading during market hours.
    - HISTORICAL_REPLAY: Simulation on historical data after hours.
    - EVOLUTION: Self-optimization mode.
    - IDLE: Waiting state.
    """

    MODES = {
        "LIVE_PAPER": "LIVE_PAPER",
        "HISTORICAL_REPLAY": "HISTORICAL_REPLAY",
        "EVOLUTION": "EVOLUTION",
        "IDLE": "IDLE"
    }

    def __init__(self, override_mode=None):
        self.current_mode = self.MODES["IDLE"]
        self.override_mode = override_mode
        self.ist = pytz.timezone("Asia/Kolkata")
        self.update_mode()

    def update_mode(self):
        """
        Determines the current mode based on time or override.
        """
        if self.override_mode:
            self.current_mode = self.override_mode
            return self.current_mode

        if SETTINGS.get("FORCE_MARKET_OPEN", False):
            self.current_mode = self.MODES["LIVE_PAPER"]
            return self.current_mode

        now_dt = datetime.now(self.ist)
        now_time = now_dt.time()
        is_weekend = now_dt.weekday() >= 5 # 5 is Saturday, 6 is Sunday

        # Market Hours: 09:15 to 15:30
        market_start = time(9, 15)
        market_end = time(15, 30)

        # Replay Hours: 16:00 to 20:00 (Example)
        replay_start = time(16, 0)
        replay_end = time(20, 0)

        # Evolution Hours: 21:00 to 23:00 (Example)
        evo_start = time(21, 0)
        evo_end = time(23, 0)

        if not is_weekend and (market_start <= now_time <= market_end):
            self.current_mode = self.MODES["LIVE_PAPER"]
        elif is_weekend or (replay_start <= now_time <= replay_end):
            # Weekends are great for historical replay and backtesting
            self.current_mode = self.MODES["HISTORICAL_REPLAY"]
        elif evo_start <= now_time <= evo_end:
            self.current_mode = self.MODES["EVOLUTION"]
        else:
            self.current_mode = self.MODES["IDLE"]

        return self.current_mode
    def get_mode(self):
        return self.current_mode

    def set_manual_override(self, mode):
        if mode in self.MODES.values() or mode is None:
            self.override_mode = mode
            self.update_mode()
        else:
            print(f"Invalid mode: {mode}")

    def is_live(self):
        return self.current_mode == self.MODES["LIVE_PAPER"]

    def is_replay(self):
        return self.current_mode == self.MODES["HISTORICAL_REPLAY"]
