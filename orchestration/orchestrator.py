import logging
from typing import Dict, Any, List
from orchestration.agents import TechnicalAgent, GreeksVolAgent, SentimentMacroAgent, RiskManagerAgent
from brain.llm_brain import LLMBrain

logger = logging.getLogger(__name__)

class MultiAgentOrchestrator:
    def __init__(self, llm_brain: LLMBrain):
        self.llm_brain = llm_brain
        self.technical_agent = TechnicalAgent()
        self.greeks_agent = GreeksVolAgent()
        self.sentiment_agent = SentimentMacroAgent()
        self.risk_agent = RiskManagerAgent()

    def run_debate_cycle(self, market_context: Dict[str, Any]) -> Dict[str, Any]:
        """Runs multi-agent debate and checks for Risk Agent veto before approving trade signals"""

        # Step 1: Collect votes from specialized agents
        tech_eval = self.technical_agent.evaluate(market_context)
        greeks_eval = self.greeks_agent.evaluate(market_context)
        sentiment_eval = self.sentiment_agent.evaluate(market_context)
        risk_eval = self.risk_agent.evaluate(market_context)

        agent_evaluations = [tech_eval, greeks_eval, sentiment_eval, risk_eval]

        # Step 2: Strict Risk VETO Check
        if risk_eval["vote"] == "VETO":
            logger.warning(f"TRADE VETOED BY RISK MANAGER: {risk_eval['reasoning']}")
            return {
                "decision": "NO_TRADE",
                "consensus_reached": False,
                "vetoed": True,
                "veto_reason": risk_eval["reasoning"],
                "agent_evaluations": agent_evaluations,
                "llm_brain_decision": None
            }

        # Step 3: LLM Brain Synthesis
        brain_decision = self.llm_brain.analyze(market_context)

        # Step 4: Consensus Thresholding
        agents_list = [self.technical_agent, self.greeks_agent, self.sentiment_agent]
        evals_list = [tech_eval, greeks_eval, sentiment_eval]

        bullish_score = sum(agent.weight * ev["confidence"] for agent, ev in zip(agents_list, evals_list) if ev["vote"] == "BULLISH")
        bearish_score = sum(agent.weight * ev["confidence"] for agent, ev in zip(agents_list, evals_list) if ev["vote"] == "BEARISH")

        final_action = brain_decision.get("action", "NO_TRADE")
        consensus = False

        if final_action == "BUY_CALL" and bullish_score >= 1.0:
            consensus = True
        elif final_action == "BUY_PUT" and bearish_score >= 1.0:
            consensus = True
        elif final_action in ["NO_TRADE", "CLOSE_POSITION"]:
            consensus = True

        return {
            "decision": final_action if consensus else "NO_TRADE",
            "consensus_reached": consensus,
            "vetoed": False,
            "bullish_score": round(bullish_score, 2),
            "bearish_score": round(bearish_score, 2),
            "agent_evaluations": agent_evaluations,
            "llm_brain_decision": brain_decision
        }
