import sys
import os
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.mode_manager import ModeManager
from core.scheduler import Scheduler
from scripts.run_live import run as run_live
from scripts.run_replay import run_replay
from scripts.run_evolution import run_evolution

def run_daily_cycle():
    mode_manager = ModeManager()
    scheduler = Scheduler(mode_manager)
    
    def live_runner():
        # In a real setup, run_live might block forever. 
        # Here we assume it runs for one iteration or is managed via a thread
        try:
            run_live()
        except KeyboardInterrupt:
            pass

    scheduler.run_daily_cycle(live_runner, run_replay, run_evolution)

if __name__ == "__main__":
    run_daily_cycle()
