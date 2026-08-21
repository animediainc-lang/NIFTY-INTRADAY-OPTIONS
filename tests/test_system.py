import pytest
import pandas as pd
from app_config.config_loader import ConfigLoader
from data.indicators import TechnicalIndicators
from data.market_data_manager import MarketDataManager
from intelligence.scanners import MarketScanner
from orchestration.consensus import MultiAgentDebateEngine
from risk.risk_manager import PositionSizer, RiskEngine
from execution.cost_model import TransactionCostModel
from execution.broker_interface import PaperBroker

def test_config_loader():
    config = ConfigLoader()
    assert config.get("trading.symbol") == "NIFTY"
    assert config.get("risk_management.max_daily_loss_pct") == 3.0

def test_technical_indicators():
    df = pd.DataFrame({
        'high': [24500, 24520, 24550, 24570, 24600],
        'low': [24480, 24490, 24510, 24530, 24550],
        'close': [24490, 24515, 24540, 24560, 24590],
        'volume': [1000, 1500, 2000, 2500, 3000]
    })
    indicators = TechnicalIndicators.get_latest_indicators(df)
    assert "vwap" in indicators
    assert "rsi_14" in indicators

def test_market_data_manager():
    mdm = MarketDataManager()
    chain = mdm.generate_option_chain(24500.0)
    assert chain.atm_strike == 24500.0
    assert len(chain.contracts) > 0
    pcr = mdm.calculate_pcr(chain.contracts)
    assert pcr > 0

def test_risk_manager_veto():
    engine = MultiAgentDebateEngine()
    snapshot = {
        'underlying_price': 24500.0,
        'india_vix': 14.5,
        'pcr': 1.3,
        'max_pain': 24500.0,
        'technical_indicators': {'vwap': 24450.0, 'ema_9': 24480.0, 'ema_20': 24460.0, 'rsi_14': 60.0}
    }
    # When daily drawdown exceeds limit (e.g. 3.5%), risk veto must trigger
    signal = engine.run_debate(snapshot, daily_loss_pct=3.5)
    assert signal.action == "NO_TRADE"
    assert signal.risk_vetoed is True

def test_position_sizer():
    sizer = PositionSizer(lot_size=25)
    lots = sizer.calculate_lots(capital=500000.0, entry_price=150.0, sl_points=30.0, max_risk_pct=1.0, max_open_lots=4)
    # Risk amount = 5000, risk/lot = 30*25 = 750 -> 5000 / 750 = 6.66 -> capped at max_open_lots 4
    assert lots == 4

def test_transaction_cost_model():
    cm = TransactionCostModel()
    costs = cm.calculate_costs(action="BUY_CE", price=150.0, quantity=50)
    assert costs["brokerage"] == 20.0
    assert costs["statutory_taxes"] > 0
    assert costs["slippage_cost"] == 75.0 # 1.5 pts * 50

def test_paper_broker_execution():
    broker = PaperBroker(initial_balance=500000.0)
    order = broker.place_order(symbol="NIFTY_24500_CE", action="BUY_CE", quantity=50, price=150.0, sl=120.0, tp=210.0)
    assert order["status"] == "OPEN"
    assert len(broker.get_positions()) == 1

    exit_order = broker.exit_position(trade_id=order["trade_id"], exit_price=180.0)
    assert exit_order["status"] == "CLOSED"
    assert exit_order["pnl"] > 0
    assert len(broker.get_positions()) == 0
