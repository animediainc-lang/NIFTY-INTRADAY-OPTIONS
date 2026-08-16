import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from logger import logger
from brain.schemas import FinalTradingSignal
from orchestration.agents import (
    LLMBrain,
    TechnicalAnalystAgent,
    GreeksVolatilityAgent,
    SentimentMacroAgent,
    RiskManagerAgent
)
from database.db_manager import DatabaseManager

class MultiAgentDebateEngine:
    """Orchestrates specialist agent debate, consensus building, and Risk Manager Veto."""

    def __init__(self):
        self.brain = LLMBrain()
        self.tech_agent = TechnicalAnalystAgent(self.brain)
        self.greeks_agent = GreeksVolatilityAgent()
        self.sentiment_agent = SentimentMacroAgent()
        self.risk_agent = RiskManagerAgent()
        self.db = DatabaseManager()

    def run_debate(
        self,
        market_snapshot: Dict[str, Any],
        daily_loss_pct: float = 0.0,
        open_positions_count: int = 0,
        max_positions: int = 2
    ) -> FinalTradingSignal:

        spot = market_snapshot.get("underlying_price", 24500.0)
        vix = market_snapshot.get("india_vix", 14.5)
        pcr = market_snapshot.get("pcr", 1.0)
        max_pain = market_snapshot.get("max_pain", spot)
        indicators = market_snapshot.get("technical_indicators", {})
        unusual_activities = market_snapshot.get("unusual_activities", [])

        # 1. Gather specialist outputs
        tech_out = self.tech_agent.analyze(indicators, spot)
        greeks_out = self.greeks_agent.analyze(vix, pcr, spot, max_pain)
        sentiment_out = self.sentiment_agent.analyze(vix, unusual_activities)

        # 2. Determine consensus proposal
        proposed_action = "NO_TRADE"
        agree_count = 0
        total_agents = 3

        if tech_out.signal == "BUY_CE" and greeks_out.pcr_signal in ["BULLISH", "NEUTRAL"]:
            proposed_action = "BUY_CE"
            agree_count = 2 if greeks_out.pcr_signal == "BULLISH" else 1.5
        elif tech_out.signal == "BUY_PE" and greeks_out.pcr_signal in ["BEARISH", "NEUTRAL"]:
            proposed_action = "BUY_PE"
            agree_count = 2 if greeks_out.pcr_signal == "BEARISH" else 1.5

        if sentiment_out.macro_bias == "BEARISH" and proposed_action == "BUY_CE":
            agree_count -= 0.5

        consensus_pct = round(agree_count / total_agents, 2)

        # 3. Apply Risk Manager Veto
        risk_out = self.risk_agent.evaluate(
            proposed_signal=proposed_action if consensus_pct >= 0.50 else "NO_TRADE",
            daily_loss_pct=daily_loss_pct,
            open_positions_count=open_positions_count,
            max_positions=max_positions
        )

        final_action = proposed_action if (risk_out.approved and consensus_pct >= 0.50) else "NO_TRADE"
        atm_strike = round(spot / 50.0) * 50.0
        option_type = "CE" if final_action == "BUY_CE" else ("PE" if final_action == "BUY_PE" else "CE")

        # Estimate option premium price (ATM call/put option premium approximation ~120-180 INR)
        estimated_option_premium = market_snapshot.get("option_premium", 150.0)

        debate_id = f"DEBATE_{uuid.uuid4().hex[:8].upper()}"

        # 4. Log debate details in Database
        self.db.log_agent_debate({
            "debate_id": debate_id,
            "timestamp": datetime.now().isoformat(),
            "underlying_price": spot,
            "vix": vix,
            "pcr": pcr,
            "tech_analysis": tech_out.model_dump(),
            "greeks_analysis": greeks_out.model_dump(),
            "sentiment_analysis": sentiment_out.model_dump(),
            "risk_assessment": risk_out.model_dump(),
            "consensus_signal": {"action": final_action, "proposed": proposed_action},
            "confidence_score": tech_out.confidence,
            "vetoed_by_risk": not risk_out.approved if proposed_action != "NO_TRADE" else False
        })

        rationale = (
            f"Tech Agent: {tech_out.signal} ({tech_out.trend}); "
            f"Greeks Agent: {greeks_out.pcr_signal} ({greeks_out.recommended_strategy}); "
            f"Risk Approval: {risk_out.approved}"
        )
        if risk_out.veto_reason:
            rationale += f" | VETO REASON: {risk_out.veto_reason}"

        return FinalTradingSignal(
            signal_id=debate_id,
            timestamp=datetime.now().isoformat(),
            symbol=f"NIFTY_{int(atm_strike)}_{option_type}",
            action=final_action,
            strike_price=atm_strike,
            option_type=option_type,
            expiry="CURRENT_WEEK",
            recommended_lots=risk_out.max_allowed_lots if final_action != "NO_TRADE" else 0,
            entry_target_range=[round(estimated_option_premium - 2, 2), round(estimated_option_premium + 2, 2)],
            stop_loss_points=30.0,
            take_profit_points=60.0,
            overall_confidence=tech_out.confidence,
            agents_consensus_pct=consensus_pct,
            risk_vetoed=not risk_out.approved if proposed_action != "NO_TRADE" else False,
            rationale=rationale
        )
