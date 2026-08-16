from typing import Dict, List, Any
import pandas as pd
from data.models import Candle
from data.indicators import TechnicalIndicators
from data.option_chain import OptionChainManager

class MarketIntelligenceScanner:
    def __init__(self, option_chain_mgr: OptionChainManager):
        self.chain_mgr = option_chain_mgr

    def scan_unusual_oi_buildup(self, oi_threshold_multiplier: float = 2.0) -> List[Dict[str, Any]]:
        """Detects option strikes experiencing abnormal OI surge"""
        anomalies = []
        for strike, contracts in self.chain_mgr.chain.items():
            for opt_type in ["CE", "PE"]:
                if opt_type in contracts:
                    contract = contracts[opt_type]
                    if contract.oi_change > 0 and contract.volume > 0:
                        # Check if OI change relative to average volume is anomalous
                        if contract.oi_change >= (contract.volume * oi_threshold_multiplier):
                            anomalies.append({
                                "symbol": contract.symbol,
                                "strike": strike,
                                "option_type": opt_type,
                                "oi_change": contract.oi_change,
                                "volume": contract.volume,
                                "reason": f"Unusual OI Surge ({contract.oi_change} vs vol {contract.volume})"
                            })
        return anomalies

    def scan_volume_spikes(self, candles: List[Candle], volume_sma_period: int = 20, multiplier: float = 2.0) -> Dict[str, Any]:
        """Detects spot or option volume surge on recent candle"""
        if not candles or len(candles) < volume_sma_period:
            return {"has_spike": False, "volume_ratio": 1.0}

        df = TechnicalIndicators.candles_to_dataframe(candles)
        recent_vol = df["volume"].iloc[-1]
        sma_vol = df["volume"].iloc[-volume_sma_period:-1].mean()

        if sma_vol > 0 and recent_vol >= (sma_vol * multiplier):
            return {
                "has_spike": True,
                "recent_volume": int(recent_vol),
                "avg_volume": round(sma_vol, 2),
                "volume_ratio": round(recent_vol / sma_vol, 2)
            }
        return {"has_spike": False, "volume_ratio": round(recent_vol / max(sma_vol, 1), 2)}

    def scan_pcr_divergence(self, pcr_history: List[float], spot_closes: List[float]) -> Dict[str, Any]:
        """Scans for sentiment divergence between spot price direction and Put-Call Ratio"""
        if len(pcr_history) < 5 or len(spot_closes) < 5:
            return {"divergence": "NEUTRAL", "reason": "Insufficient history"}

        spot_trend = spot_closes[-1] - spot_closes[-5]
        pcr_trend = pcr_history[-1] - pcr_history[-5]

        # Bullish divergence: Spot making lower low / downward trend, but PCR sharply rising (> 1.2)
        if spot_trend < 0 and pcr_trend > 0.2 and pcr_history[-1] >= 1.2:
            return {"divergence": "BULLISH_REVERSAL", "reason": "Spot falling but PCR rapidly rising above 1.2"}

        # Bearish divergence: Spot making higher high / upward trend, but PCR sharply falling (< 0.7)
        if spot_trend > 0 and pcr_trend < -0.2 and pcr_history[-1] <= 0.7:
            return {"divergence": "BEARISH_REVERSAL", "reason": "Spot rising but PCR rapidly dropping below 0.7"}

        return {"divergence": "NEUTRAL", "reason": "No sentiment divergence detected"}
