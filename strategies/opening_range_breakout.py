from strategies.base_strategy import BaseStrategy
import pandas as pd
from datetime import time

class OpeningRangeBreakout(BaseStrategy):
    def __init__(self, range_minutes: int = 15):
        super().__init__(f"{range_minutes}min ORB")
        self.range_minutes = range_minutes
        self.market_open = time(9, 15)
        self.range_high = None
        self.range_low = None

    def _calculate_range(self):
        """Calculates the high and low of the first N minutes of the actual market day."""
        if self.data is None or len(self.data) == 0:
            return

        df = self.data
        # Ensure we only use today's data starting from 09:15
        today = df.index[-1].date()
        open_time = pd.Timestamp.combine(today, self.market_open)
        range_end_time = open_time + pd.Timedelta(minutes=self.range_minutes)

        range_data = df[(df.index >= open_time) & (df.index < range_end_time)]
        if not range_data.empty:
            self.range_high = range_data['high'].max()
            self.range_low = range_data['low'].min()

    def check_entry(self) -> bool:
        if self.data is None or len(self.data) < 2:
            return False

        self._calculate_range()
        if self.range_high is None:
            return False

        df = self.data
        current_time = df.index[-1]
        today = current_time.date()
        range_end_time = pd.Timestamp.combine(today, self.market_open) + pd.Timedelta(minutes=self.range_minutes)

        if current_time <= range_end_time:
            return False

        current_price = df['close'].iloc[-1]
        current_vol = df['volume'].iloc[-1]
        avg_vol = df['volume'].tail(5).mean()

        return current_price > self.range_high and current_vol > avg_vol

    def check_exit(self) -> bool:
        if self.data is None or self.range_low is None:
            return False
        return self.data['close'].iloc[-1] < self.range_low
