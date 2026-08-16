import pytest
from datetime import datetime
from data.models import Candle, OptionContract, TickData
from data.greeks import GreeksEngine
from data.option_chain import OptionChainManager
from data.indicators import TechnicalIndicators
from intelligence.scanners import MarketIntelligenceScanner
from brain.llm_brain import LLMBrain
from orchestration.agents import RiskManagerAgent
from orchestration.orchestrator import MultiAgentOrchestrator
from execution.costs import IndianTransactionCostEngine
from risk.risk_manager import RiskEngine
from execution.order_manager import PaperOrderManager
from data.broker_client import MockPaperBrokerClient

def test_options_greeks():
    price = GreeksEngine.calculate_price(S=24000, K=24000, T=7/365, r=0.07, sigma=0.15, option_type="CE")
    greeks = GreeksEngine.calculate_greeks(S=24000, K=24000, T=7/365, r=0.07, sigma=0.15, option_type="CE")
    assert price > 0
    assert 0.4 < greeks["delta"] < 0.6
    assert greeks["gamma"] > 0

def test_option_chain_pcr_max_pain():
    mgr = OptionChainManager()
    c1 = OptionContract(symbol="CE1", strike_price=24000, option_type="CE", expiry="2024-10-31", open_interest=10000)
    c2 = OptionContract(symbol="PE1", strike_price=24000, option_type="PE", expiry="2024-10-31", open_interest=15000)
    mgr.update_contract(c1, 24000, 7/365)
    mgr.update_contract(c2, 24000, 7/365)

    assert mgr.calculate_pcr() == 1.5
    assert mgr.calculate_max_pain() == 24000

def test_technical_indicators():
    candles = [
        Candle(timestamp=datetime(2024,10,24,9,15+i), open=24000+i, high=24005+i, low=23995+i, close=24002+i, volume=1000)
        for i in range(20)
    ]
    df = TechnicalIndicators.candles_to_dataframe(candles)
    vwap = TechnicalIndicators.calculate_vwap(df)
    rsi = TechnicalIndicators.calculate_rsi(df)
    assert not vwap.empty
    assert not rsi.empty

def test_risk_manager_veto():
    brain = LLMBrain(provider="mock")
    orchestrator = MultiAgentOrchestrator(brain)
    ctx = {'spot_price': 24050, 'vwap': 24000, 'rsi': 65, 'pcr': 1.25, 'vix': 14.0, 'current_daily_loss': 4000.0}
    res = orchestrator.run_debate_cycle(ctx)
    assert res["decision"] == "NO_TRADE"
    assert res["vetoed"] is True

def test_transaction_cost_engine():
    cost_eng = IndianTransactionCostEngine()
    costs = cost_eng.calculate_trade_costs(buy_price=100.0, sell_price=130.0, quantity=50)
    assert costs["gross_pnl"] == 1500.0
    assert costs["total_taxes_and_charges"] > 0
    assert costs["net_pnl"] < costs["gross_pnl"]

def test_paper_execution_flow():
    broker = MockPaperBrokerClient()
    broker.connect()
    cost_eng = IndianTransactionCostEngine()
    risk_eng = RiskEngine(total_capital=100000.0)
    order_mgr = PaperOrderManager(broker, risk_eng, cost_eng)

    signal = {'decision': 'BUY_CALL', 'llm_brain_decision': {'suggested_stop_loss_points': 15.0, 'suggested_target_points': 30.0}}
    pos = order_mgr.execute_signal(signal, 'NIFTY24OCT24000CE', 100.0, datetime(2024, 10, 24, 10, 0))
    assert pos is not None
    assert pos["symbol"] == 'NIFTY24OCT24000CE'

    exits = order_mgr.update_positions('NIFTY24OCT24000CE', 135.0, datetime(2024, 10, 24, 10, 15))
    assert len(exits) == 1
    assert exits[0]["exit_reason"] == "TARGET_HIT"
