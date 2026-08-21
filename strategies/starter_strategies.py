from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import pandas as pd

class BaseStrategy(ABC):
    """Abstract Base Class for Options Trading Strategies."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def generate_signal(self, df_candles: pd.DataFrame, market_snapshot: Dict[str, Any]) -> Dict[str, Any]:
        """Generates trading signal dict given market candles and snapshot data."""
        pass

class DirectionalMomentumBuyer(BaseStrategy):
    """Strategy 1: Intraday Directional Options Buyer targeting quick momentum breaks."""

    def __init__(self):
        super().__init__("Directional Momentum Buyer")

    def generate_signal(self, df_candles: pd.DataFrame, market_snapshot: Dict[str, Any]) -> Dict[str, Any]:
        if len(df_candles) < 15:
            return {"action": "NO_TRADE", "reason": "Insufficient candle data"}

        latest = df_candles.iloc[-1]
        vwap = market_snapshot.get("technical_indicators", {}).get("vwap", latest["close"])
        rsi = market_snapshot.get("technical_indicators", {}).get("rsi_14", 50)
        spot = market_snapshot.get("underlying_price", latest["close"])
        pcr = market_snapshot.get("pcr", 1.0)

        # Bullish momentum breakout: Price > VWAP, RSI > 58, PCR > 1.0
        if latest["close"] > vwap and rsi > 58 and pcr >= 1.0:
            return {
                "action": "BUY_CE",
                "strategy": self.name,
                "confidence": 0.80,
                "stop_loss_points": 25.0,
                "take_profit_points": 50.0,
                "reason": "Bullish VWAP breakout + RSI momentum"
            }

        # Bearish momentum breakdown: Price < VWAP, RSI < 42, PCR < 0.85
        elif latest["close"] < vwap and rsi < 42 and pcr <= 0.85:
            return {
                "action": "BUY_PE",
                "strategy": self.name,
                "confidence": 0.80,
                "stop_loss_points": 25.0,
                "take_profit_points": 50.0,
                "reason": "Bearish VWAP breakdown + RSI breakdown"
            }

        return {"action": "NO_TRADE", "reason": "No momentum trigger"}

class IronCondorSeller(BaseStrategy):
    """Strategy 2: Hedged Premium Seller (Iron Condor / Short Strangle) in low/normal vol environments."""

    def __init__(self):
        super().__init__("Hedged Premium Seller (Iron Condor)")

    def generate_signal(self, df_candles: pd.DataFrame, market_snapshot: Dict[str, Any]) -> Dict[str, Any]:
        vix = market_snapshot.get("india_vix", 14.0)
        pcr = market_snapshot.get("pcr", 1.0)
        rsi = market_snapshot.get("technical_indicators", {}).get("rsi_14", 50)

        # Sideways regime: VIX 12-18, RSI 45-55, PCR 0.9-1.1
        if 12.0 <= vix <= 18.0 and 45 <= rsi <= 55 and 0.90 <= pcr <= 1.10:
            return {
                "action": "IRON_CONDOR",
                "strategy": self.name,
                "confidence": 0.75,
                "call_short_strike_offset": 150.0,
                "put_short_strike_offset": 150.0,
                "wing_offset": 100.0,
                "stop_loss_points": 35.0,
                "take_profit_points": 45.0,
                "reason": "Mean-reverting rangebound regime detected"
            }

        return {"action": "NO_TRADE", "reason": "Market directional bias active"}

class VolatilityBreakoutBuyer(BaseStrategy):
    """Strategy 3: Intraday Volatility Breakout Buyer capitalizing on VIX spikes & Bollinger Squeezes."""

    def __init__(self):
        super().__init__("Volatility Breakout Buyer")

    def generate_signal(self, df_candles: pd.DataFrame, market_snapshot: Dict[str, Any]) -> Dict[str, Any]:
        vix = market_snapshot.get("india_vix", 14.0)
        bb_upper = market_snapshot.get("technical_indicators", {}).get("bb_upper", 0.0)
        bb_lower = market_snapshot.get("technical_indicators", {}).get("bb_lower", 0.0)
        spot = market_snapshot.get("underlying_price", 24500.0)

        if vix >= 16.0 and spot > bb_upper and bb_upper > 0:
            return {
                "action": "BUY_CE",
                "strategy": self.name,
                "confidence": 0.85,
                "stop_loss_points": 30.0,
                "take_profit_points": 70.0,
                "reason": "Upper Bollinger Band expansion breakout with elevated VIX"
            }
        elif vix >= 16.0 and spot < bb_lower and bb_lower > 0:
            return {
                "action": "BUY_PE",
                "strategy": self.name,
                "confidence": 0.85,
                "stop_loss_points": 30.0,
                "take_profit_points": 70.0,
                "reason": "Lower Bollinger Band expansion breakdown with elevated VIX"
            }

        return {"action": "NO_TRADE", "reason": "Volatility squeeze dormant"}
