import numpy as np
import pandas as pd
from typing import Dict, Any, List

class TechnicalIndicators:
    """Calculates intraday technical indicators for Nifty spot & option charts."""

    @staticmethod
    def calculate_ema(series: pd.Series, period: int) -> pd.Series:
        return series.ewm(span=period, adjust=False).mean()

    @staticmethod
    def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss.replace(0, 1e-9)
        return 100 - (100 / (1 + rs))

    @staticmethod
    def calculate_vwap(df: pd.DataFrame) -> pd.Series:
        """Calculates Session VWAP anchored to daily open."""
        typical_price = (df["high"] + df["low"] + df["close"]) / 3
        cum_tp_vol = (typical_price * df["volume"]).cumsum()
        cum_vol = df["volume"].cumsum().replace(0, 1e-9)
        return cum_tp_vol / cum_vol

    @staticmethod
    def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        high_low = df["high"] - df["low"]
        high_close = (df["high"] - df["close"].shift()).abs()
        low_close = (df["low"] - df["close"].shift()).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return tr.rolling(period).mean()

    @staticmethod
    def calculate_bollinger_bands(series: pd.Series, period: int = 20, std_dev: float = 2.0) -> Dict[str, pd.Series]:
        sma = series.rolling(period).mean()
        std = series.rolling(period).std()
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        return {"upper": upper, "middle": sma, "lower": lower}

    @classmethod
    def get_latest_indicators(cls, df: pd.DataFrame) -> Dict[str, float]:
        """Convenience method returning latest candle's indicator values."""
        if len(df) < 20:
            return {
                "ema_9": df["close"].iloc[-1] if not df.empty else 0.0,
                "ema_20": df["close"].iloc[-1] if not df.empty else 0.0,
                "rsi_14": 50.0,
                "vwap": df["close"].iloc[-1] if not df.empty else 0.0,
                "atr_14": 0.0,
                "bb_upper": df["close"].iloc[-1] if not df.empty else 0.0,
                "bb_lower": df["close"].iloc[-1] if not df.empty else 0.0
            }

        ema_9 = cls.calculate_ema(df["close"], 9).iloc[-1]
        ema_20 = cls.calculate_ema(df["close"], 20).iloc[-1]
        rsi_14 = cls.calculate_rsi(df["close"], 14).iloc[-1]
        vwap = cls.calculate_vwap(df).iloc[-1]
        atr_14 = cls.calculate_atr(df, 14).iloc[-1]
        bb = cls.calculate_bollinger_bands(df["close"], 20, 2.0)

        return {
            "ema_9": float(ema_9),
            "ema_20": float(ema_20),
            "rsi_14": float(rsi_14),
            "vwap": float(vwap),
            "atr_14": float(atr_14) if not np.isnan(atr_14) else 0.0,
            "bb_upper": float(bb["upper"].iloc[-1]),
            "bb_lower": float(bb["lower"].iloc[-1])
        }
