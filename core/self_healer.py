import os
import shutil
import time
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(filename='healer.log', level=logging.INFO, format='%(asctime)s - %(message)s')

BACKUP_DIR = "backups/stable_snapshot"
SOURCE_DIRS = ["core", "engines"]
MAIN_FILE = "main.py"

class SelfHealer:
    def __init__(self):
        self.crash_count = 0
        self.last_crash_time = 0
        self.boot_time = time.time()

    def mark_system_stable(self):
        """
        Agar system 5 minute tak bina crash hue chala, 
        toh current code ko 'Stable' mark karke backup le lo.
        """
        run_duration = time.time() - self.boot_time
        if run_duration > 300: # 5 minutes
            self.create_snapshot()
            return True
        return False

    def create_snapshot(self):
        """Current working code ka backup leta hai."""
        try:
            if not os.path.exists(BACKUP_DIR):
                os.makedirs(BACKUP_DIR)
            
            # Backup Core Folders
            for folder in SOURCE_DIRS:
                src = folder
                dst = os.path.join(BACKUP_DIR, folder)
                if os.path.exists(dst):
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
            
            # Backup Main Script
            shutil.copy2(MAIN_FILE, os.path.join(BACKUP_DIR, MAIN_FILE))
            
            logging.info("✅ System Stable. Code snapshot saved.")
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 🛡️ Self-Healer: Code marked as STABLE. Backup taken.")
        except Exception as e:
            logging.error(f"Snapshot Failed: {e}")

    def restore_stable_snapshot(self):
        """Crash hone par purana stable code wapas lata hai."""
        try:
            if not os.path.exists(BACKUP_DIR):
                print("❌ No stable backup found! Cannot restore.")
                return False

            print(f"[{datetime.now().strftime('%H:%M:%S')}] 🚑 Self-Healer: Critical Crash Detected! Restoring last stable code...")
            
            # Restore Core Folders
            for folder in SOURCE_DIRS:
                src = os.path.join(BACKUP_DIR, folder)
                dst = folder
                if os.path.exists(src):
                    if os.path.exists(dst):
                        shutil.rmtree(dst)
                    shutil.copytree(src, dst)

            # Restore Main Script
            src_main = os.path.join(BACKUP_DIR, MAIN_FILE)
            if os.path.exists(src_main):
                shutil.copy2(src_main, MAIN_FILE)

            logging.info("✅ System Restored to last stable version.")
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ System Restored! Restarting...")
            return True
        except Exception as e:
            logging.error(f"Restore Failed: {e}")
            return False

    def report_crash(self):
        """Crash count badhata hai aur check karta hai ki restore ki zaroorat hai ya nahi."""
        current_time = time.time()
        
        # Agar pichla crash 2 min ke andar hua tha, toh count badhao
        if current_time - self.last_crash_time < 120:
            self.crash_count += 1
        else:
            self.crash_count = 1 # Reset counter if crash happened long ago
        
        self.last_crash_time = current_time
        
        print(f"⚠️ Crash Count: {self.crash_count}/3")
        
        if self.crash_count >= 3:
            self.restore_stable_snapshot()
            self.crash_count = 0 # Reset after restore
