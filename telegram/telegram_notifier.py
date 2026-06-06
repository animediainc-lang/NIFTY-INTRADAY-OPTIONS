import requests
from app_config.config_loader import config
from logger import logger
from typing import Dict, Any, Optional

class TelegramNotifier:
    def __init__(self):
        self.bot_token = None
        self.chat_id = None
        self.enabled = False

    def _initialize(self):
        """Lazily initialize token and chat_id from config."""
        self.bot_token = config.get("telegram.bot_token")
        self.chat_id = config.get("telegram.chat_id")
        self.enabled = bool(self.bot_token and self.chat_id)

    def send_message(self, message: str):
        """Sends a text message via Telegram."""
        self._initialize()
        if not self.enabled:
            return

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }

        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code != 200:
                logger.error(f"Telegram error: {response.text}")
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")

    def notify_market_open(self, metrics: Dict[str, Any]):
        msg = (
            "🔔 *Market Open Summary*\n"
            f"VIX: {metrics.get('vix', 'N/A')}\n"
            f"PCR: {metrics.get('pcr', 'N/A')}\n"
            f"Max Pain: {metrics.get('max_pain', 'N/A')}\n"
            f"PDH: {metrics.get('pdh', 'N/A')} | PDL: {metrics.get('pdl', 'N/A')}"
        )
        self.send_message(msg)

    def notify_trade_entry(self, trade: Dict[str, Any]):
        msg = (
            "🚀 *Trade Entered*\n"
            f"Symbol: `{trade.get('symbol')}`\n"
            f"Strategy: {trade.get('strategy')}\n"
            f"Entry: {trade.get('entry_price')}\n"
            f"Qty: {trade.get('quantity')}\n"
            f"SL: {trade.get('stop_loss')}"
        )
        self.send_message(msg)

    def notify_trade_exit(self, trade: Dict[str, Any], exit_price: float, pnl: float):
        status = "✅ Profit" if pnl > 0 else "❌ Loss"
        msg = (
            f"{status} *Trade Closed*\n"
            f"Symbol: `{trade.get('symbol')}`\n"
            f"Exit: {exit_price}\n"
            f"PnL: {pnl:.2f}"
        )
        self.send_message(msg)

    def notify_error(self, error_msg: str):
        self.send_message(f"⚠️ *System Error*\n`{error_msg}`")

# Global Notifier
notifier = TelegramNotifier()
