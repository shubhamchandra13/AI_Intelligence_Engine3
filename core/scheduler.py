import time
from datetime import datetime
from core.mode_manager import ModeManager

class Scheduler:
    """
    Automates the daily cycle: Live trading -> Historical Replay -> Evolution.
    """
    def __init__(self, mode_manager: ModeManager):
        self.mode_manager = mode_manager
        self.last_replay_date = None
        self.last_evolution_date = None

    def run_daily_cycle(self, live_runner, replay_runner, evolution_runner):
        print("Starting Automated Daily Cycle...")
        
        while True:
            self.mode_manager.update_mode()
            current_mode = self.mode_manager.get_mode()
            
            now = datetime.now()
            today_str = now.strftime("%Y-%m-%d")

            if current_mode == "LIVE_PAPER":
                print(f"[{now.time()}] Operating in LIVE_PAPER mode...")
                live_runner()
                
            elif current_mode == "HISTORICAL_REPLAY":
                if self.last_replay_date != today_str:
                    print(f"[{now.time()}] Triggering HISTORICAL_REPLAY mode...")
                    replay_runner()
                    self.last_replay_date = today_str
                else:
                    print(f"[{now.time()}] Replay already completed for today. Idling...")
                    time.sleep(60)
                    
            elif current_mode == "EVOLUTION":
                if self.last_evolution_date != today_str:
                    print(f"[{now.time()}] Triggering EVOLUTION mode...")
                    evolution_runner()
                    self.last_evolution_date = today_str
                else:
                    print(f"[{now.time()}] Evolution already completed for today. Idling...")
                    time.sleep(60)
                    
            else: # IDLE
                print(f"[{now.time()}] System is IDLE. Waiting for next window...")
                time.sleep(60)
