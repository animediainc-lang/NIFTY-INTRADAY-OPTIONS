import pandas as pd
import numpy as np
from typing import List, Dict, Any
from data.models import Candle

class TechnicalIndicators:
    @staticmethod
    def candles_to_dataframe(candles: List[Candle]) -> pd.DataFrame:
        if not candles:
            return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume", "open_interest"])
        data = [{
            "timestamp": c.timestamp,
            "open": c.open,
            "high": c.high,
            "low": c.low,
            "close": c.close,
            "volume": c.volume,
            "open_interest": c.open_interest
        } for c in candles]
        df = pd.DataFrame(data)
        df.sort_values("timestamp", inplace=True)
        df.reset_index(drop=True, inplace=True)
        return df

    @staticmethod
    def calculate_vwap(df: pd.DataFrame) -> pd.Series:
        """Intraday Cumulative Volume Weighted Average Price"""
        if df.empty or "volume" not in df.columns:
            return pd.Series(dtype=float)
        typical_price = (df["high"] + df["low"] + df["close"]) / 3.0
        cum_tp_vol = (typical_price * df["volume"]).cumsum()
        cum_vol = df["volume"].cumsum()
        vwap = cum_tp_vol / np.maximum(cum_vol, 1)
        return round(vwap, 2)

    @staticmethod
    def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Relative Strength Index"""
        if df.empty or len(df) < period:
            return pd.Series(dtype=float)
        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / np.maximum(loss, 1e-6)
        rsi = 100 - (100 / (1 + rs))
        return round(rsi, 2)

    @staticmethod
    def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Average True Range"""
        if df.empty or len(df) < period:
            return pd.Series(dtype=float)
        high_low = df["high"] - df["low"]
        high_close = (df["high"] - df["close"].shift()).abs()
        low_close = (df["low"] - df["close"].shift()).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        return round(atr, 2)

    @staticmethod
    def calculate_ema(df: pd.DataFrame, period: int = 20) -> pd.Series:
        """Exponential Moving Average"""
        if df.empty or len(df) < period:
            return pd.Series(dtype=float)
        ema = df["close"].ewm(span=period, adjust=False).mean()
        return round(ema, 2)

    @staticmethod
    def calculate_supertrend(df: pd.DataFrame, period: int = 10, multiplier: float = 3.0) -> pd.DataFrame:
        """SuperTrend Indicator returning trend line and direction (+1 bullish, -1 bearish)"""
        if df.empty or len(df) < period:
            return pd.DataFrame(columns=["supertrend", "direction"])

        atr = TechnicalIndicators.calculate_atr(df, period)
        hl2 = (df["high"] + df["low"]) / 2.0
        basic_ub = hl2 + (multiplier * atr)
        basic_lb = hl2 - (multiplier * atr)

        final_ub = pd.Series(0.0, index=df.index)
        final_lb = pd.Series(0.0, index=df.index)
        supertrend = pd.Series(0.0, index=df.index)
        direction = pd.Series(1, index=df.index)

        for i in range(1, len(df)):
            final_ub.iloc[i] = basic_ub.iloc[i] if basic_ub.iloc[i] < final_ub.iloc[i-1] or df["close"].iloc[i-1] > final_ub.iloc[i-1] else final_ub.iloc[i-1]
            final_lb.iloc[i] = basic_lb.iloc[i] if basic_lb.iloc[i] > final_lb.iloc[i-1] or df["close"].iloc[i-1] < final_lb.iloc[i-1] else final_lb.iloc[i-1]

            if direction.iloc[i-1] == 1:
                if df["close"].iloc[i] < final_lb.iloc[i]:
                    direction.iloc[i] = -1
                    supertrend.iloc[i] = final_ub.iloc[i]
                else:
                    direction.iloc[i] = 1
                    supertrend.iloc[i] = final_lb.iloc[i]
            else:
                if df["close"].iloc[i] > final_ub.iloc[i]:
                    direction.iloc[i] = 1
                    supertrend.iloc[i] = final_lb.iloc[i]
                else:
                    direction.iloc[i] = -1
                    supertrend.iloc[i] = final_ub.iloc[i]

        return pd.DataFrame({"supertrend": round(supertrend, 2), "direction": direction})
