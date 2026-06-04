from strategies.base_strategy import BaseStrategy
from strategies.indicators import calculate_ema
import pandas as pd

class TrendContinuation(BaseStrategy):
    def __init__(self):
        super().__init__("Trend Continuation Pullback")

    def check_entry(self) -> bool:
        if self.data is None or len(self.data) < 20:
            return False

        df = self.data.copy()
        df['ema_fast'] = calculate_ema(df, period=9)
        df['ema_slow'] = calculate_ema(df, period=21)

        current_price = df['close'].iloc[-1]
        prev_price = df['close'].iloc[-2]
        ema_fast = df['ema_fast'].iloc[-1]
        ema_slow = df['ema_slow'].iloc[-1]

        # Conditions:
        # 1. Trend established (Fast EMA > Slow EMA)
        # 2. Pullback (Previous Close was near or below Fast EMA)
        # 3. Momentum Resumption (Current Close > Fast EMA and > Previous High)
        cond_trend = ema_fast > ema_slow
        cond_pullback = prev_price <= (ema_fast * 1.002) # within 0.2% of EMA
        cond_resumption = current_price > ema_fast and current_price > df['high'].iloc[-2]

        oi_support = True
        if 'oi' in df.columns:
            oi_support = df['oi'].iloc[-1] >= df['oi'].iloc[-5:].mean()

        return cond_trend and cond_pullback and cond_resumption and oi_support

    def check_exit(self) -> bool:
        if self.data is None or len(self.data) < 2:
            return False

        # Exit if trend reverses (Fast EMA < Slow EMA)
        df = self.data.copy()
        df['ema_fast'] = calculate_ema(df, period=9)
        df['ema_slow'] = calculate_ema(df, period=21)
        return df['ema_fast'].iloc[-1] < df['ema_slow'].iloc[-1]
