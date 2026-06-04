import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from logger import logger

class CandleManager:
    def __init__(self, intervals: List[int] = [1, 3, 5]):
        self.intervals = intervals
        # instrument_key -> interval -> DataFrame (OHLC)
        self.candles: Dict[str, Dict[int, pd.DataFrame]] = {}

    def process_tick(self, tick: Dict[str, Any]):
        """Processes an incoming tick and updates only the necessary candle."""
        try:
            symbol = tick.get("stock_code")
            if not symbol:
                return

            last_price = float(tick.get("last", 0))
            timestamp_str = tick.get("datetime")
            if not timestamp_str:
                return

            timestamp = pd.to_datetime(timestamp_str)

            if symbol not in self.candles:
                self.candles[symbol] = {interval: pd.DataFrame(columns=["open", "high", "low", "close"]) for interval in self.intervals}

            for interval in self.intervals:
                self._update_interval_candle(symbol, interval, timestamp, last_price)

        except Exception as e:
            logger.error(f"Error processing tick for {tick.get('stock_code')}: {e}")

    def _update_interval_candle(self, symbol: str, interval: int, timestamp: datetime, price: float):
        """Updates or creates a candle for a specific interval."""
        # Calculate candle start time (e.g., 9:15:23 -> 9:15:00 for 1min)
        candle_start = timestamp.replace(second=0, microsecond=0)
        if interval > 1:
            minute = (candle_start.minute // interval) * interval
            candle_start = candle_start.replace(minute=minute)

        df = self.candles[symbol][interval]

        if not df.empty and candle_start in df.index:
            # Update existing candle
            df.at[candle_start, "high"] = max(df.at[candle_start, "high"], price)
            df.at[candle_start, "low"] = min(df.at[candle_start, "low"], price)
            df.at[candle_start, "close"] = price
        else:
            # Create new candle
            new_candle = pd.DataFrame(
                [{"open": price, "high": price, "low": price, "close": price}],
                index=[candle_start]
            )
            self.candles[symbol][interval] = pd.concat([df, new_candle])

            # Keep only last 100 candles
            if len(self.candles[symbol][interval]) > 100:
                self.candles[symbol][interval] = self.candles[symbol][interval].iloc[-100:]

    def get_candles(self, symbol: str, interval: int) -> Optional[pd.DataFrame]:
        """Returns the candle dataframe for a specific symbol and interval."""
        return self.candles.get(symbol, {}).get(interval)

    def get_latest_candle(self, symbol: str, interval: int) -> Optional[Dict[str, Any]]:
        """Returns the most recently closed (not active) candle."""
        df = self.get_candles(symbol, interval)
        if df is not None and len(df) > 1:
            return df.iloc[-2].to_dict()
        return None

# Global candle manager
candle_manager = CandleManager()
