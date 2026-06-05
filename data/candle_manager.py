import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from logger import logger

class CandleManager:
    def __init__(self, intervals: List[int] = [1, 3, 5]):
        self.intervals = intervals
        self.candles: Dict[str, Dict[int, pd.DataFrame]] = {}
        self.last_ttq: Dict[str, float] = {}
        self.on_candle_closed_callbacks = []
        # Persistent storage for morning range (09:15 - 09:45)
        self.morning_candles: Dict[str, Dict[int, pd.DataFrame]] = {}

    def add_candle_callback(self, callback):
        self.on_candle_closed_callbacks.append(callback)

    def process_tick(self, tick: Dict[str, Any]):
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

            if symbol not in self.last_ttq:
                self.last_ttq[symbol] = current_ttq
                vol_delta = 0
            else:
                vol_delta = max(0, current_ttq - self.last_ttq[symbol])
                self.last_ttq[symbol] = current_ttq

            if symbol not in self.candles:
                self.candles[symbol] = {
                    i: pd.DataFrame(columns=["open", "high", "low", "close", "volume", "oi"]) for i in self.intervals
                }
                self.morning_candles[symbol] = {
                    i: pd.DataFrame(columns=["open", "high", "low", "close", "volume", "oi"]) for i in self.intervals
                }

            for interval in self.intervals:
                self._update_interval_candle(symbol, interval, timestamp, last_price, vol_delta, last_oi)

        except Exception as e:
            logger.error(f"Error processing tick for {tick.get('stock_code')}: {e}")

    def _update_interval_candle(self, symbol: str, interval: int, timestamp: datetime, price: float, vol_delta: float, oi: float):
        candle_start = timestamp.replace(second=0, microsecond=0)
        if interval > 1:
            minute = (candle_start.minute // interval) * interval
            candle_start = candle_start.replace(minute=minute)

        # Update sliding window
        df = self.candles[symbol][interval]
        self.candles[symbol][interval] = self._apply_update(df, candle_start, price, vol_delta, oi, symbol, interval, True)

        # Update persistent morning window if applicable
        if candle_start.hour == 9 and candle_start.minute < 45:
            m_df = self.morning_candles[symbol][interval]
            self.morning_candles[symbol][interval] = self._apply_update(m_df, candle_start, price, vol_delta, oi, symbol, interval, False)

    def _apply_update(self, df, candle_start, price, vol_delta, oi, symbol, interval, trigger_callback):
        if not df.empty and candle_start in df.index:
            df.at[candle_start, "high"] = max(float(df.at[candle_start, "high"]), price)
            df.at[candle_start, "low"] = min(float(df.at[candle_start, "low"]), price)
            df.at[candle_start, "close"] = price
            df.at[candle_start, "volume"] = float(df.at[candle_start, "volume"]) + vol_delta
            df.at[candle_start, "oi"] = oi
        else:
            if trigger_callback and not df.empty:
                closed_candle = df.iloc[-1].to_dict()
                closed_candle['timestamp'] = df.index[-1]
                closed_candle['symbol'] = symbol
                closed_candle['interval'] = interval
                for cb in self.on_candle_closed_callbacks:
                    cb(closed_candle)

            new_row = pd.DataFrame(
                [{"open": price, "high": price, "low": price, "close": price, "volume": vol_delta, "oi": oi}],
                index=[candle_start]
            ).astype(float)
            df = pd.concat([df, new_row])

            if trigger_callback and len(df) > 100:
                df = df.iloc[-100:]
        return df

    def get_candles(self, symbol: str, interval: int) -> Optional[pd.DataFrame]:
        df_sliding = self.candles.get(symbol, {}).get(interval)
        df_morning = self.morning_candles.get(symbol, {}).get(interval)
        if df_sliding is not None and df_morning is not None:
             return pd.concat([df_morning, df_sliding]).drop_duplicates().sort_index()
        return df_sliding

    def get_latest_candle(self, symbol: str, interval: int) -> Optional[Dict[str, Any]]:
        df = self.get_candles(symbol, interval)
        if df is not None and len(df) > 1:
            return df.iloc[-2].to_dict()
        return None

# Global candle manager
candle_manager = CandleManager()
