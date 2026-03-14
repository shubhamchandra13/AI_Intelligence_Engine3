import os
from datetime import datetime

import requests
from dotenv import load_dotenv


load_dotenv(override=True)


class TelegramNotifier:

    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.enabled = bool(self.token and self.chat_id)

    def send(self, message):
        if not self.enabled:
            return False

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "disable_web_page_preview": True,
        }
        try:
            resp = requests.post(url, data=payload, timeout=10)
            return resp.status_code == 200
        except Exception:
            return False

    def _num(self, value, default=0.0):
        try:
            if value is None:
                return default
            return float(value)
        except Exception:
            return default

    def format_entry_message(self, position, snapshot=None):
        snap = snapshot or {}
        regime = (snap.get("regime") or {}).get("regime") if isinstance(snap.get("regime"), dict) else snap.get("regime")
        confidence = snap.get("confidence")
        stat_prob = (snap.get("stat_probability") or {}).get("win_probability")
        ml_prob = (snap.get("ml_probability") or {}).get("win_probability")
        meta = snap.get("meta_label") or {}
        reason_lines = [
            f"Bias: {snap.get('structure_bias')}",
            f"Regime: {regime}",
            f"Confidence: {confidence}",
            f"StatWinProb: {stat_prob}",
            f"MLWinProb: {ml_prob}",
            f"MetaRec: {meta.get('recommendation')}",
        ]
        reason_text = "\n".join(reason_lines)

        return (
            "TRADE OPENED\n"
            f"UTC: {datetime.utcnow().isoformat()}\n"
            f"Index: {position.get('index')}\n"
            f"Direction: {position.get('direction')}\n"
            f"Entry: {round(self._num(position.get('entry')), 2)}\n"
            f"Lots: {position.get('lots')} | Qty: {position.get('total_qty')}\n"
            f"Stop: {round(self._num(position.get('stop')), 2)} | Target: {round(self._num(position.get('target')), 2)}\n"
            f"Capital Used: {round(self._num(position.get('capital_used')), 2)}\n"
            "Why Taken:\n"
            f"{reason_text}"
        )

    def format_exit_message(self, trade_data):
        pnl = trade_data.get("pnl", 0)
        return (
            "TRADE CLOSED\n"
            f"UTC: {datetime.utcnow().isoformat()}\n"
            f"Index: {trade_data.get('index')}\n"
            f"Direction: {trade_data.get('direction')}\n"
            f"Entry: {round(self._num(trade_data.get('entry_price')), 2)} | Exit: {round(self._num(trade_data.get('exit_price')), 2)}\n"
            f"PnL: {round(pnl, 2)}\n"
            f"Result: {'PROFIT' if pnl > 0 else 'LOSS'}\n"
            f"Reason: {trade_data.get('exit_reason')}\n"
            f"Regime: {trade_data.get('regime')} | IV: {trade_data.get('iv_regime')}"
        )
