import json
import requests
from typing import Dict, Any, Optional
from app_config.config_loader import ConfigLoader
from logger import logger
from brain.schemas import (
    TechnicalAnalysisOutput,
    GreeksAnalysisOutput,
    SentimentAnalysisOutput,
    RiskAssessmentOutput
)

class LLMBrain:
    """Interface for Claude/LLM structured reasoning."""

    def __init__(self):
        self.config = ConfigLoader()
        self.api_key = self.config.get("ai_brain.api_key", "")
        self.model = self.config.get("ai_brain.model", "claude-3-5-sonnet-20241022")

    def query_claude_json(self, system_prompt: str, user_prompt: str) -> Optional[Dict[str, Any]]:
        """Invokes Claude API or falls back to rule-based structured response if API key is missing/invalid."""
        if not self.api_key or "MISSING" in self.api_key:
            logger.debug("No valid Claude API key found. Using internal rule-based inference engine.")
            return None

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

        payload = {
            "model": self.model,
            "max_tokens": 1500,
            "temperature": 0.2,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": user_prompt}
            ]
        }

        try:
            res = requests.post("https://api.anthropic.com/v1/messages", json=payload, headers=headers, timeout=10)
            if res.status_code == 200:
                data = res.json()
                text = data["content"][0]["text"]
                return json.loads(text)
            else:
                logger.warning(f"Claude API error ({res.status_code}): {res.text}")
                return None
        except Exception as e:
            logger.error(f"Failed to query LLM Brain: {e}")
            return None

class TechnicalAnalystAgent:
    """Specialist agent analyzing technical patterns, VWAP, EMA, RSI."""

    def __init__(self, brain: LLMBrain):
        self.brain = brain

    def analyze(self, indicators: Dict[str, float], spot_price: float) -> TechnicalAnalysisOutput:
        vwap = indicators.get("vwap", spot_price)
        ema_9 = indicators.get("ema_9", spot_price)
        ema_20 = indicators.get("ema_20", spot_price)
        rsi = indicators.get("rsi_14", 50.0)

        # Quantitative logic determination
        if spot_price > vwap and ema_9 > ema_20 and rsi > 55:
            trend = "BULLISH"
            signal = "BUY_CE"
            confidence = 0.85
            drivers = ["Price above VWAP", "EMA 9/20 Golden Cross", "RSI Momentum > 55"]
        elif spot_price < vwap and ema_9 < ema_20 and rsi < 45:
            trend = "BEARISH"
            signal = "BUY_PE"
            confidence = 0.85
            drivers = ["Price below VWAP", "EMA 9/20 Bearish Death Cross", "RSI Momentum < 45"]
        else:
            trend = "NEUTRAL"
            signal = "NO_TRADE"
            confidence = 0.60
            drivers = ["Price oscillating near VWAP", "RSI in neutral range (45-55)"]

        return TechnicalAnalysisOutput(
            trend=trend,
            signal=signal,
            support_level=round(spot_price - 80, 2),
            resistance_level=round(spot_price + 80, 2),
            confidence=confidence,
            key_drivers=drivers
        )

class GreeksVolatilityAgent:
    """Specialist agent analyzing IV, PCR, Max Pain, and options Greeks."""

    def analyze(self, vix: float, pcr: float, spot_price: float, max_pain: float) -> GreeksAnalysisOutput:
        if vix < 12.0:
            iv_regime = "LOW_VOL"
        elif vix <= 18.0:
            iv_regime = "NORMAL_VOL"
        else:
            iv_regime = "HIGH_VOL"

        if pcr >= 1.2:
            pcr_signal = "BULLISH"
            rec = "BUY_CALL"
        elif pcr <= 0.8:
            pcr_signal = "BEARISH"
            rec = "BUY_PUT"
        else:
            pcr_signal = "NEUTRAL"
            rec = "IRON_CONDOR" if iv_regime == "HIGH_VOL" else "NO_TRADE"

        return GreeksAnalysisOutput(
            iv_regime=iv_regime,
            pcr_signal=pcr_signal,
            recommended_strategy=rec,
            delta_exposure=0.50 if pcr_signal == "BULLISH" else (-0.50 if pcr_signal == "BEARISH" else 0.0),
            confidence=0.80,
            reasoning=f"PCR sits at {pcr} indicating {pcr_signal} bias. India VIX is {vix} ({iv_regime}). Max Pain is at {max_pain}."
        )

class SentimentMacroAgent:
    """Specialist agent parsing market intelligence, unusual activities, and VIX sentiment."""

    def analyze(self, vix: float, unusual_activities: list) -> SentimentAnalysisOutput:
        vix_bias = "RISK_OFF" if vix > 18.0 else ("RISK_ON" if vix < 13.0 else "NEUTRAL")
        macro_bias = "BEARISH" if vix_bias == "RISK_OFF" else "NEUTRAL"

        summary = f"Detected {len(unusual_activities)} unusual option chain events."
        return SentimentAnalysisOutput(
            macro_bias=macro_bias,
            unusual_activity_summary=summary,
            vix_bias=vix_bias,
            confidence=0.75
        )

class RiskManagerAgent:
    """Agent with absolute VETO POWER over trades based on risk rules."""

    def evaluate(self, proposed_signal: str, daily_loss_pct: float, open_positions_count: int, max_positions: int) -> RiskAssessmentOutput:
        if proposed_signal == "NO_TRADE":
            return RiskAssessmentOutput(approved=False, risk_score=50.0, max_allowed_lots=0, veto_reason="No action proposed.")

        if daily_loss_pct >= 3.0:
            return RiskAssessmentOutput(
                approved=False,
                risk_score=0.0,
                max_allowed_lots=0,
                veto_reason=f"CRITICAL: Daily drawdown limit reached ({daily_loss_pct:.2f}% >= 3.0%). Kill switch engaged."
            )

        if open_positions_count >= max_positions:
            return RiskAssessmentOutput(
                approved=False,
                risk_score=20.0,
                max_allowed_lots=0,
                veto_reason=f"Maximum allowed open positions limit reached ({open_positions_count}/{max_positions})."
            )

        return RiskAssessmentOutput(
            approved=True,
            risk_score=85.0,
            max_allowed_lots=2,
            veto_reason=None
        )
