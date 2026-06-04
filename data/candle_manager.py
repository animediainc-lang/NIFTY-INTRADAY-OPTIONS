import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from logger import logger

class CandleManager:
    def __init__(self, intervals: List[int] = [1, 3, 5]):
        self.intervals = intervals
        # instrument_key -> interval -> DataFrame (OHLCV + OI)
        self.candles: Dict[str, Dict[int, pd.DataFrame]] = {}
        # Track last TTQ to calculate interval volume
        self.last_ttq: Dict[str, float] = {}
        # Callbacks for closed candles
        self.on_candle_closed_callbacks = []

    def add_candle_callback(self, callback):
        self.on_candle_closed_callbacks.append(callback)

    def process_tick(self, tick: Dict[str, Any]):
        """Processes an incoming tick and updates only the necessary candle."""
        try:
            symbol = tick.get("stock_code")
            if not symbol:
                return

            last_price = float(tick.get("last", 0))
            current_ttq = float(tick.get("v", tick.get("ttq", 0)))
            last_oi = float(tick.get("oi", 0))
            timestamp_str = tick.get("datetime")
            if not timestamp_str:
                return

            timestamp = pd.to_datetime(timestamp_str)

            # Volume delta logic
            if symbol not in self.last_ttq:
                self.last_ttq[symbol] = current_ttq
                vol_delta = 0
            else:
                vol_delta = max(0, current_ttq - self.last_ttq[symbol])
                self.last_ttq[symbol] = current_ttq

            if symbol not in self.candles:
                self.candles[symbol] = {
                    interval: pd.DataFrame(columns=["open", "high", "low", "close", "volume", "oi"])
                    for interval in self.intervals
                }

            for interval in self.intervals:
                self._update_interval_candle(symbol, interval, timestamp, last_price, vol_delta, last_oi)

        except Exception as e:
            logger.error(f"Error processing tick for {tick.get('stock_code')}: {e}")

    def _update_interval_candle(self, symbol: str, interval: int, timestamp: datetime, price: float, vol_delta: float, oi: float):
        """Updates or creates a candle for a specific interval."""
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
            df.at[candle_start, "volume"] += vol_delta
            df.at[candle_start, "oi"] = oi
        else:
            # A new candle is starting
            if not df.empty:
                closed_candle = df.iloc[-1].to_dict()
                closed_candle['timestamp'] = df.index[-1]
                closed_candle['symbol'] = symbol
                closed_candle['interval'] = interval
                for cb in self.on_candle_closed_callbacks:
                    cb(closed_candle)

            # Create new candle
            new_candle = pd.DataFrame(
                [{"open": price, "high": price, "low": price, "close": price, "volume": vol_delta, "oi": oi}],
                index=[candle_start]
            )
            self.candles[symbol][interval] = pd.concat([df, new_candle])

            if len(self.candles[symbol][interval]) > 100:
                self.candles[symbol][interval] = self.candles[symbol][interval].iloc[-100:]

    def get_candles(self, symbol: str, interval: int) -> Optional[pd.DataFrame]:
        return self.candles.get(symbol, {}).get(interval)

    def get_latest_candle(self, symbol: str, interval: int) -> Optional[Dict[str, Any]]:
        """Returns the most recently closed (not active) candle."""
        df = self.get_candles(symbol, interval)
        if df is not None and len(df) > 1:
            return df.iloc[-2].to_dict()
        return None

# Global candle manager
candle_manager = CandleManager()
