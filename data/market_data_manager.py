import math
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from data.models import OptionChain, OptionContract, OptionType, MarketSnapshot
from logger import logger

class MarketDataManager:
    """Simulates/fetches real-time market data, option chain, VIX, PCR, Max Pain, and Greeks."""

    def __init__(self, step_size: float = 50.0):
        self.step_size = step_size
        self.underlying_price = 24500.0
        self.india_vix = 14.5
        self.candle_history: List[Dict[str, Any]] = []

    def get_atm_strike(self, spot_price: float) -> float:
        return round(spot_price / self.step_size) * self.step_size

    def calculate_pcr(self, contracts: Dict[str, OptionContract]) -> float:
        """Put-Call Ratio based on total Open Interest."""
        total_put_oi = sum(c.oi for c in contracts.values() if c.option_type == OptionType.PUT)
        total_call_oi = sum(c.oi for c in contracts.values() if c.option_type == OptionType.CALL)
        if total_call_oi == 0:
            return 1.0
        return round(total_put_oi / total_call_oi, 2)

    def calculate_max_pain(self, contracts: Dict[str, OptionContract]) -> float:
        """Calculates Max Pain strike price where option sellers incur minimal payout."""
        strikes = sorted(list(set(c.strike for c in contracts.values())))
        if not strikes:
            return self.get_atm_strike(self.underlying_price)

        min_loss = float("inf")
        max_pain_strike = strikes[0]

        for strike_eval in strikes:
            total_loss = 0.0
            for c in contracts.values():
                if c.option_type == OptionType.CALL and strike_eval > c.strike:
                    total_loss += (strike_eval - c.strike) * c.oi
                elif c.option_type == OptionType.PUT and strike_eval < c.strike:
                    total_loss += (c.strike - strike_eval) * c.oi

            if total_loss < min_loss:
                min_loss = total_loss
                max_pain_strike = strike_eval

        return max_pain_strike

    def generate_option_chain(self, spot_price: float, expiry_str: str = "CURRENT_WEEK") -> OptionChain:
        """Generates realistic synthetic Option Chain around current spot price."""
        atm_strike = self.get_atm_strike(spot_price)
        strikes = [atm_strike + i * self.step_size for i in range(-10, 11)]

        contracts = {}
        for s in strikes:
            # Call contract
            call_key = f"{int(s)}_CE"
            call_intrinsic = max(0.0, spot_price - s)
            call_extrinsic = max(5.0, 150.0 - abs(spot_price - s) * 0.15)
            call_price = round(call_intrinsic + call_extrinsic, 2)
            call_oi = int(max(10000, 250000 - abs(spot_price - s) * 150))

            contracts[call_key] = OptionContract(
                symbol=f"NIFTY{call_key}",
                strike=s,
                option_type=OptionType.CALL,
                expiry=expiry_str,
                ltp=call_price,
                iv=self.india_vix + (s - spot_price) * 0.01,
                delta=round(0.5 + (spot_price - s) / 500.0, 2),
                oi=call_oi,
                change_in_oi=int(call_oi * 0.05),
                volume=int(call_oi * 0.2)
            )

            # Put contract
            put_key = f"{int(s)}_PE"
            put_intrinsic = max(0.0, s - spot_price)
            put_extrinsic = max(5.0, 150.0 - abs(spot_price - s) * 0.15)
            put_price = round(put_intrinsic + put_extrinsic, 2)
            put_oi = int(max(10000, 230000 - abs(spot_price - s) * 140))

            contracts[put_key] = OptionContract(
                symbol=f"NIFTY{put_key}",
                strike=s,
                option_type=OptionType.PUT,
                expiry=expiry_str,
                ltp=put_price,
                iv=self.india_vix + (spot_price - s) * 0.01,
                delta=round(-0.5 + (spot_price - s) / 500.0, 2),
                oi=put_oi,
                change_in_oi=int(put_oi * 0.04),
                volume=int(put_oi * 0.18)
            )

        return OptionChain(
            timestamp=datetime.now(),
            underlying_price=spot_price,
            atm_strike=atm_strike,
            contracts=contracts
        )
