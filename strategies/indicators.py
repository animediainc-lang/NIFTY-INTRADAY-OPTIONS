import pandas as pd
import numpy as np

def calculate_vwap(df: pd.DataFrame) -> pd.Series:
    """
    Calculates session-anchored Volume Weighted Average Price.
    Expects a DatetimeIndex.
    """
    df = df.copy()
    df['tp'] = (df['high'] + df['low'] + df['close']) / 3
    df['tp_v'] = df['tp'] * df['volume']

    # Cumulative sum anchored by date
    groups = df.groupby(df.index.date)
    cum_tp_v = groups['tp_v'].cumsum()
    cum_v = groups['volume'].cumsum()

    return cum_tp_v / cum_v

def calculate_ema(df: pd.DataFrame, period: int = 20) -> pd.Series:
    """Calculates Exponential Moving Average."""
    return df['close'].ewm(span=period, adjust=False).mean()

def calculate_volume_sma(df: pd.DataFrame, period: int = 20) -> pd.Series:
    """Calculates Simple Moving Average of Volume."""
    return df['volume'].rolling(window=period).mean()

def is_hhhl(df: pd.DataFrame, lookback: int = 3) -> bool:
    """Checks for Higher High Higher Low structure."""
    if len(df) < lookback + 1:
        return False

    current_high = df['high'].iloc[-1]
    current_low = df['low'].iloc[-1]

    prev_high = df['high'].iloc[-lookback-1:-1].max()
    prev_low = df['low'].iloc[-lookback-1:-1].min()

    return current_high > prev_high and current_low > prev_low
