import queue
import threading
import time
from engines.telegram_notifier import TelegramNotifier

class SafeNotifier:
    """
    Thread-safe asynchronous notifier to prevent UI hangs.
    """
    def __init__(self):
        self.notifier = TelegramNotifier()
        self.queue = queue.Queue()
        self.worker = threading.Thread(target=self._process_queue, daemon=True)
        self.worker.start()

    def _process_queue(self):
        while True:
            try:
                # Get message from queue
                msg = self.queue.get()
                if msg is None: break
                
                # Send to Telegram (with internal timeout)
                self.notifier.send(msg)
                
                # Mark as done
                self.queue.task_done()
                time.sleep(1) # Rate limit protection
            except:
                pass

    def notify_entry(self, position, snapshot=None):
        try:
            msg = self.notifier.format_entry_message(position, snapshot)
            self.queue.put(msg)
        except: pass

    def notify_exit(self, trade_data):
        try:
            msg = self.notifier.format_exit_message(trade_data)
            self.queue.put(msg)
        except: pass

    def notify_alert(self, text):
        try:
            msg = f"🔔 SYSTEM ALERT\n{text}"
            self.queue.put(msg)
        except: pass

    def send(self, msg):
        """Generic send method for compatibility."""
        try:
            self.queue.put(msg)
        except: pass

    # --- FOR BACKWARD COMPATIBILITY WITH format_message calls ---
    def format_entry_message(self, position, snapshot=None):
        return self.notifier.format_entry_message(position, snapshot)

    def format_exit_message(self, trade_data):
        return self.notifier.format_exit_message(trade_data)
