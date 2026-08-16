import json
import logging
import requests
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

CLAUDE_SYSTEM_PROMPT = """You are the AI Reasoning Brain of a high-frequency algorithmic options trading system for Indian Equity Derivatives (NSE Nifty 50).
Your task is to analyze real-time market context, technical indicators, options chain metrics (Greeks, PCR, Max Pain), and unusual intelligence scans to make precise intraday option trading decisions.

You MUST respond strictly with a valid JSON object following this exact schema:
{
  "action": "BUY_CALL" | "BUY_PUT" | "NO_TRADE" | "CLOSE_POSITION",
  "strike_type": "ATM" | "ITM1" | "OTM1" | "NONE",
  "confidence_score": <float between 0.0 and 1.0>,
  "reasoning_summary": "<brief 1-2 sentence explanation>",
  "technical_confluence": "<key technical rationale>",
  "greeks_analysis": "<delta/gamma/vega rationale>",
  "market_regime": "TRENDING_UP" | "TRENDING_DOWN" | "RANGE_BOUND" | "HIGH_VOLATILITY",
  "suggested_stop_loss_points": <float option premium SL in points>,
  "suggested_target_points": <float option premium Target in points>
}

Do NOT include any markdown code blocks, preamble, or conversational commentary outside of the single valid JSON string.
"""

class LLMBrain:
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-5-sonnet-20241022", provider: str = "mock"):
        self.api_key = api_key
        self.model = model
        self.provider = provider

    def build_prompt(self, market_context: Dict[str, Any]) -> str:
        """Construct structured user prompt containing current market state"""
        return f"""Current Market State Analysis:
- Nifty Spot Price: {market_context.get('spot_price', 'N/A')}
- VWAP: {market_context.get('vwap', 'N/A')}
- RSI (14): {market_context.get('rsi', 'N/A')}
- SuperTrend Direction: {market_context.get('supertrend_direction', 'N/A')}
- Put-Call Ratio (PCR): {market_context.get('pcr', 'N/A')}
- Max Pain Strike: {market_context.get('max_pain', 'N/A')}
- ATM Straddle IV: {market_context.get('atm_iv', 'N/A')}
- Scanners Anomalies: {market_context.get('scanner_anomalies', [])}
- Active Positions: {market_context.get('active_positions', [])}

Evaluate market confluence and return the structured JSON decision.
"""

    def parse_and_validate_response(self, raw_text: str) -> Dict[str, Any]:
        """Validates JSON structure and fallback defaults if parsing fails"""
        try:
            cleaned = raw_text.strip()
            # Extract content between first '{' and last '}' if extra text is present
            start_idx = cleaned.find("{")
            end_idx = cleaned.rfind("}")
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                cleaned = cleaned[start_idx:end_idx+1]

            parsed = json.loads(cleaned)
            required_keys = ["action", "strike_type", "confidence_score", "reasoning_summary"]
            for key in required_keys:
                if key not in parsed:
                    raise ValueError(f"Missing required key in LLM JSON: {key}")

            return parsed
        except Exception as e:
            logger.error(f"Failed to parse LLM JSON output: {e}. Raw text: {raw_text}")
            return {
                "action": "NO_TRADE",
                "strike_type": "NONE",
                "confidence_score": 0.0,
                "reasoning_summary": f"Parse error: {str(e)}",
                "technical_confluence": "N/A",
                "greeks_analysis": "N/A",
                "market_regime": "UNKNOWN",
                "suggested_stop_loss_points": 0.0,
                "suggested_target_points": 0.0
            }

    def analyze(self, market_context: Dict[str, Any]) -> Dict[str, Any]:
        """Calls LLM provider or generates deterministic rule-based mock response"""
        prompt = self.build_prompt(market_context)

        if self.provider == "anthropic" and self.api_key and self.api_key != "MOCK_LLM_KEY":
            try:
                headers = {
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                }
                payload = {
                    "model": self.model,
                    "max_tokens": 500,
                    "temperature": 0.1,
                    "system": CLAUDE_SYSTEM_PROMPT,
                    "messages": [{"role": "user", "content": prompt}]
                }
                response = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload, timeout=10)
                if response.status_code == 200:
                    raw_content = response.json()["content"][0]["text"]
                    return self.parse_and_validate_response(raw_content)
                else:
                    logger.error(f"Anthropic API error: {response.status_code} - {response.text}")
            except Exception as e:
                logger.error(f"Error calling Anthropic API: {e}")

        # Deterministic Mock Fallback Logic for testing
        spot = market_context.get("spot_price", 24000)
        vwap = market_context.get("vwap", 24000)
        rsi = market_context.get("rsi", 50)
        pcr = market_context.get("pcr", 1.0)

        if spot > vwap and rsi > 60 and pcr > 1.0:
            mock_json = json.dumps({
                "action": "BUY_CALL",
                "strike_type": "ATM",
                "confidence_score": 0.85,
                "reasoning_summary": "Bullish breakout above VWAP with strong RSI and supportive PCR.",
                "technical_confluence": "Spot > VWAP, RSI 62",
                "greeks_analysis": "Positive Delta momentum, manageable Theta decay",
                "market_regime": "TRENDING_UP",
                "suggested_stop_loss_points": 15.0,
                "suggested_target_points": 30.0
            })
        elif spot < vwap and rsi < 40 and pcr < 0.8:
            mock_json = json.dumps({
                "action": "BUY_PUT",
                "strike_type": "ATM",
                "confidence_score": 0.82,
                "reasoning_summary": "Bearish breakdown below VWAP with oversold RSI and weak PCR.",
                "technical_confluence": "Spot < VWAP, RSI 38",
                "greeks_analysis": "Negative Delta exposure, sharp Gamma burst",
                "market_regime": "TRENDING_DOWN",
                "suggested_stop_loss_points": 15.0,
                "suggested_target_points": 30.0
            })
        else:
            mock_json = json.dumps({
                "action": "NO_TRADE",
                "strike_type": "NONE",
                "confidence_score": 0.30,
                "reasoning_summary": "Market in range-bound consolidation near VWAP. No clear directional edge.",
                "technical_confluence": "Spot oscillating near VWAP",
                "greeks_analysis": "Neutral",
                "market_regime": "RANGE_BOUND",
                "suggested_stop_loss_points": 0.0,
                "suggested_target_points": 0.0
            })

        return self.parse_and_validate_response(mock_json)
