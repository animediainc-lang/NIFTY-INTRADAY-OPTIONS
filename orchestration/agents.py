import logging
from abc import ABC, abstractmethod
from typing import Dict, Any

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    def __init__(self, name: str, weight: float = 1.0):
        self.name = name
        self.weight = weight

    @abstractmethod
    def evaluate(self, market_context: Dict[str, Any]) -> Dict[str, Any]:
        """Returns vote: {'agent': name, 'vote': 'BULLISH'|'BEARISH'|'NEUTRAL'|'VETO', 'confidence': float, 'reasoning': str}"""
        pass


class TechnicalAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="Technical Specialist Agent", weight=1.2)

    def evaluate(self, market_context: Dict[str, Any]) -> Dict[str, Any]:
        spot = market_context.get("spot_price", 0)
        vwap = market_context.get("vwap", 0)
        rsi = market_context.get("rsi", 50)
        supertrend_dir = market_context.get("supertrend_direction", 1)

        if spot > vwap and rsi > 55 and supertrend_dir == 1:
            return {
                "agent": self.name,
                "vote": "BULLISH",
                "confidence": 0.85,
                "reasoning": f"Spot ({spot}) > VWAP ({vwap}), RSI is bullish ({rsi}), SuperTrend is Up."
            }
        elif spot < vwap and rsi < 45 and supertrend_dir == -1:
            return {
                "agent": self.name,
                "vote": "BEARISH",
                "confidence": 0.85,
                "reasoning": f"Spot ({spot}) < VWAP ({vwap}), RSI is bearish ({rsi}), SuperTrend is Down."
            }
        else:
            return {
                "agent": self.name,
                "vote": "NEUTRAL",
                "confidence": 0.5,
                "reasoning": "Mixed technical indicators; market range-bound."
            }


class GreeksVolAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="Options Greeks & Volatility Agent", weight=1.0)

    def evaluate(self, market_context: Dict[str, Any]) -> Dict[str, Any]:
        pcr = market_context.get("pcr", 1.0)
        vix = market_context.get("vix", 15.0)

        if vix > 25.0:
            return {
                "agent": self.name,
                "vote": "NEUTRAL",
                "confidence": 0.4,
                "reasoning": f"India VIX elevated at {vix}. High premium decay risk."
            }

        if pcr >= 1.2:
            return {
                "agent": self.name,
                "vote": "BULLISH",
                "confidence": 0.8,
                "reasoning": f"Strong Put-Call Ratio of {pcr} indicates bullish put writing support."
            }
        elif pcr <= 0.7:
            return {
                "agent": self.name,
                "vote": "BEARISH",
                "confidence": 0.8,
                "reasoning": f"Low Put-Call Ratio of {pcr} indicates heavy call writing overhead."
            }
        else:
            return {
                "agent": self.name,
                "vote": "NEUTRAL",
                "confidence": 0.5,
                "reasoning": f"PCR of {pcr} is balanced in neutral territory."
            }


class SentimentMacroAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="Sentiment & Intelligence Agent", weight=0.8)

    def evaluate(self, market_context: Dict[str, Any]) -> Dict[str, Any]:
        anomalies = market_context.get("scanner_anomalies", [])
        if any("Unusual OI" in a.get("reason", "") for a in anomalies):
            return {
                "agent": self.name,
                "vote": "BULLISH",
                "confidence": 0.75,
                "reasoning": "Unusual institutional OI buildup detected in options chain."
            }
        return {
            "agent": self.name,
            "vote": "NEUTRAL",
            "confidence": 0.5,
            "reasoning": "No extreme market intelligence divergence detected."
        }


class RiskManagerAgent(BaseAgent):
    """Risk Agent holds STRICT VETO power over all trades"""
    def __init__(self, max_daily_loss_limit: float = 3000.0):
        super().__init__(name="Risk Manager Agent (VETO POWER)", weight=999.0)
        self.max_daily_loss_limit = max_daily_loss_limit

    def evaluate(self, market_context: Dict[str, Any]) -> Dict[str, Any]:
        current_daily_loss = market_context.get("current_daily_loss", 0.0)
        consecutive_losses = market_context.get("consecutive_losses", 0)
        vix = market_context.get("vix", 15.0)

        # Hard Veto Checks
        if current_daily_loss >= self.max_daily_loss_limit:
            return {
                "agent": self.name,
                "vote": "VETO",
                "confidence": 1.0,
                "reasoning": f"Daily loss limit breached ({current_daily_loss} >= {self.max_daily_loss_limit}). KILL SWITCH ACTIVATED."
            }

        if consecutive_losses >= 3:
            return {
                "agent": self.name,
                "vote": "VETO",
                "confidence": 1.0,
                "reasoning": f"3 consecutive losses recorded ({consecutive_losses}). Trading halted."
            }

        if vix > 28.0:
            return {
                "agent": self.name,
                "vote": "VETO",
                "confidence": 1.0,
                "reasoning": f"Extreme volatility spike (India VIX {vix} > 28.0). Capital preservation trigger."
            }

        return {
            "agent": self.name,
            "vote": "APPROVED",
            "confidence": 1.0,
            "reasoning": "All risk parameters within safety limits."
        }
