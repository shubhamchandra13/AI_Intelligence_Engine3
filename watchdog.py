import subprocess
import time
import os
import sys
import threading
from datetime import datetime
from core.self_healer import SelfHealer

# Configuration
TARGET_SCRIPT = "main.py"
RESTART_DELAY = 5 # seconds
LOG_FILE = "watchdog_log.txt"
CAPTURE_FILE = "capture.txt"
CAPTURE_ERR_FILE = "capture_err.txt"

# Initialize Self-Healer
healer = SelfHealer()

def log_event(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg = f"[{timestamp}] {message}"
    try:
        print(msg)
        with open(LOG_FILE, "a") as f:
            f.write(msg + "\n")
    except: pass

def run_engine():
    """Runs the main trading engine and monitors its exit code."""
    log_event(f"Starting Engine: {TARGET_SCRIPT}...")
    
    start_time = time.time()
    
    try:
        # Use simple subprocess call to avoid complex threading issues in watchdog
        # This keeps the main terminal clean and lets main.py handle its own UI
        process = subprocess.Popen([sys.executable, TARGET_SCRIPT])
        process.wait()
        return_code = process.returncode
    except KeyboardInterrupt:
        return_code = 0
    except Exception as e:
        log_event(f"Execution Error: {e}")
        return_code = 1

    # --- SELF-HEALING LOGIC ---
    run_duration = time.time() - start_time
    
    if run_duration > 300: # 5 Minutes Stable Run
        if healer.mark_system_stable():
            log_event("System marked as STABLE by Healer.")
    else:
        # Crash happened quickly! Report to Healer
        log_event(f"Quick Crash detected ({round(run_duration,1)}s). Reporting to Healer...")
        healer.report_crash()

    if return_code != 0:
        log_event(f"Engine CRASHED with exit code {return_code}.")
    else:
        log_event("Engine SHUT DOWN gracefully.")

def main():
    log_event("WATCHDOG ACTIVE: Monitoring Trading Engine...")
    
    while True:
        try:
            run_engine()
        except KeyboardInterrupt:
            log_event("Watchdog Stopped by User.")
            break
        except Exception as e:
            log_event(f"Watchdog Critical Error: {e}")
            
        log_event(f"Restarting in {RESTART_DELAY} seconds...")
        time.sleep(RESTART_DELAY)

if __name__ == "__main__":
    main()
