from strategies.base_strategy import BaseStrategy
from strategies.indicators import calculate_vwap, calculate_volume_sma, is_hhhl
import pandas as pd

class MomentumBreakout(BaseStrategy):
    def __init__(self):
        super().__init__("Momentum Breakout")

    def check_entry(self) -> bool:
        if self.data is None or len(self.data) < 20:
            return False

        df = self.data.copy()
        df['vwap'] = calculate_vwap(df)
        df['vol_sma'] = calculate_volume_sma(df, period=20)

        current_price = df['close'].iloc[-1]
        vwap = df['vwap'].iloc[-1]
        current_vol = df['volume'].iloc[-1]
        vol_sma = df['vol_sma'].iloc[-1]

        # Conditions:
        # 1. Price above VWAP
        # 2. HHHL structure
        # 3. Volume expansion
        # 4. OI confirmation (assuming 'oi' column exists in dataframe)
        cond_vwap = current_price > vwap
        cond_hhhl = is_hhhl(df)
        cond_vol = current_vol > (vol_sma * 1.5)

        oi_confirmed = True
        if 'oi' in df.columns:
            oi_confirmed = df['oi'].iloc[-1] > df['oi'].iloc[-2]

        return cond_vwap and cond_hhhl and cond_vol and oi_confirmed

    def check_exit(self) -> bool:
        if self.data is None or len(self.data) < 2:
            return False

        # Simple exit: price falls below VWAP
        df = self.data.copy()
        df['vwap'] = calculate_vwap(df)
        return df['close'].iloc[-1] < df['vwap'].iloc[-1]
